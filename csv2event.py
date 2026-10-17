#!/usr/bin/env python3
"""Generate a static OpenADR 3 (price) event from a CSV file.

This includes helpers for processing CSV files and generating
a proper event and top level code to convert a two-column
CSV file to a JSON file.
"""

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

def read_csv(csv_path, selector=(0, 1)):
	"""Read timestamp and values from the specified CSV columns.

	A single optional header row is accepted. Empty rows are ignored. The
	timestamps must be strictly increasing so interval durations are unambiguous.

	'selector' is a tuple specifying which columns (0 based indices) to use.
	The first item is converted into a datetime object and all others into
	floats.

	Returns a list of tuples. Each tuple represents a valid data row and has
	the same length as 'selector'.
	"""
	records = []
	columns_needed = max(selector) + 1
	reader = csv.reader(csv_path.open("r", newline="", encoding="utf-8-sig"))
	for row in reader:
		if not row or all(not cell.strip() for cell in row):
			continue
		
		if len(row) < columns_needed:
			raise ValueError(f"line {reader.line_num}: expected at least {columns_needed} columns")

		values = [row[i].strip() for i in selector]
		try:
			timestamp = datetime.fromisoformat(values[0])
			values = map(float, values[1:])
		except:
			if reader.line_num == 1:
				# Accept common headers such as timestamp,price.
				continue
			raise ValueError(f"I don't understand line {reader.line_num}")
		records.append((timestamp, *values))

	return records


def format_timestamp(timestamp: datetime) -> str:
	"""Format a timestamp as ISO 8601 with a Z suffix."""
	return timestamp.isoformat(timespec="seconds").replace("+00:00", "Z")


def duration_to_iso8601(duration):
	"""Convert a whole-second timedelta to an OpenADR duration."""
	seconds = int(duration.total_seconds())
	if seconds != duration.total_seconds():
		raise ValueError("timestamp differences must be whole seconds")
	days, seconds = divmod(seconds, 86400)
	hours, seconds = divmod(seconds, 3600)
	minutes, seconds = divmod(seconds, 60)
	result = "P"
	if days:
		result += f"{days}D"
	if hours or minutes or seconds:
		result += "T"
		if hours:
			result += f"{hours}H"
		if minutes:
			result += f"{minutes}M"
		if seconds:
			result += f"{seconds}S"

	if result == "P":
		raise ValueError("A duration of 0 is pointless and not supported")

	return result


def make_event(records, programID, type='PRICE', payloadDescriptor=None, id=None):
	"""
	Build an openADR event from a list of (timestamp, value) tuples.

	Timestamps need not be evenly spaced, but at least two are required;
	otherwise no interval durations can be inferred. Because the last interval
	has no defined duration, it is assumed to equal the one before it.

	Args:
	  records: the list of (timestamp, value) tuples
	  programID: the objectID of the program the event belongs to
	  type: What kind of event is it? (default: 'PRICE')
	  payloadDescriptor (dict): optional JSON object
	  id (URL safe string): objectID of the event
	      If missing, a default value is generated based on 'programID'.

	Returns:
	  The generated event as dict.
	"""

	if len(records) < 2:
		raise ValueError("Can't infer duration without at least 2 timestamps")
	if id == None:
		id = programID + "-event"
	elif id.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"):
		raise ValueError("objectID doesn't match pattern '^[a-zA-Z0-9_-]*$': " + id)
	now = format_timestamp(datetime.now(timezone.utc))
	intervals = []
	for index in range(len(records)):
		start, value = records[index]
		if index + 1 < len(records):
			duration = records[index + 1][0] - start
		if duration <= timedelta(0):
			raise ValueError("timestamps must be strictly increasing")
		intervals.append(
			{
				"id": index,
				"intervalPeriod": {
					"start": format_timestamp(start),
					"duration": duration_to_iso8601(duration),
				},
				"payloads": [{"type": type, "values": [value]}],
			}
		)

	event = {
		"id": id,
		"objectType": "EVENT",
		"createdDateTime": now,
		"modificationDateTime": now,
		"programID": programID,
		"priority": 0,
		"intervals": intervals,
	}

	if payloadDescriptor != None:
		event['payloadDescriptors'] = [payloadDescriptor]

	return event


def main():
	parser = argparse.ArgumentParser(description='Generate openADR events as static files from CSV files')
	parser.add_argument("csv_file", type=Path, help="CSV containing timestamp and data columns")
	parser.add_argument("program_file", type=Path, help="program to which the event will belong")
	parser.add_argument("-t", "--type", help="the type of event to generate")
	parser.add_argument(
		"-o", "--output",
		type=Path,
		help="event JSON output path (default: relative to program_file)",
	)
	args = parser.parse_args()
	try:
		program = json.load(args.program_file.open('r'))
		t = args.type
		try:
			plD = program['payloadDescriptors']
			if len(plD) == 1:
				plD = plD[0]
				t = plD['payloadType']
				if args.type != None and args.type != t:
					print("Warning: Ignoring bad event type from arguments", file=sys.stderr)
			else:
				plD = plD[[d['payloadType'] for d in plD].index(t)]
		except IndexError:
			plD = None
			print("Warning: No payloadDescriptor found in", args.program_file, file=sys.stderr)
		if args.output != None:
			output = args.output
		else:
			output = args.program_file.parents[1].joinpath('events', program['id'] + '-event-' + t)
		event = make_event(read_csv(args.csv_file), program['id'], t, plD, output.name)
		output.parent.mkdir(parents=True, exist_ok=True)
		output.write_text(json.dumps(event, indent=2) + "\n", encoding="utf-8")
	except (OSError, ValueError) as exc:
		print(f"error: {exc}", file=sys.stderr)
		return 2
	print(f"wrote {output}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

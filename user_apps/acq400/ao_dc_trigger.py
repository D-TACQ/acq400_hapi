#!/usr/bin/env python3

"""
Set a value for each channel to output on DACs on trigger

Usage:
    # Set immediate value and triggered value using hex (DAC codes)
    ./user_apps/acq400/ao_dc_trigger.py 0x0000,0x0000,0x0000,0x0000 0x1fff,0x3fff,0x5fff,0x7fff acq1001_070

    # Set immediate value and triggered value using floats (voltages)
    ./user_apps/acq400/ao_dc_trigger.py 0.0,0.0,0.0,0.0 0.75,1.5,2.25,3.0 acq1001_070

    # Set immediate value only (only valid after UUT has been triggered)
    ./user_apps/acq400/ao_dc_trigger.py 0,0,0,0 acq1001_070
"""
import argparse
import acq400_hapi


def is_comma_separated_hexes(input_string):
    """Parse input strings of hexes e.g. 0x0000,0x0000,0x0000,0x0000
    into lists"""
    values = input_string.split(",")
    for value in values:
        if value.lower().startswith("0x"):
            pass
        else:
            return False
    return ",".join(values)


def parse_voltages(input_string, encoding, vmin, vmax, bits):
    values = input_string.split(",")

    for idx, value in enumerate(values):
        if value.lower().startswith("0x"):
            raise ValueError("Do not mix voltage floats and hex codes")
        values[idx] = _convert_voltage(value, encoding, vmin, vmax, bits)
    return ",".join(values)


def _convert_voltage(val, encoding, vmin, vmax, bits):
    """Convert integer codes to voltages based on choice of encoding,
    defined voltage range and bit-depth."""
    # Clamp voltage to configured range
    v_val = max(vmin, min(vmax, float(val)))
    # Calculate normalized position (0.0 to 1.0)
    span = vmax - vmin
    norm = 0.0 if span == 0 else (v_val - vmin) / span

    max_val = (1 << bits) - 1
    half_range = 1 << (bits - 1)

    if encoding == "twos_complement":
        # Signed range mapping
        val = round(norm * max_val - half_range)
        if val < 0:
            val += 1 << bits
    elif encoding == "offset_binary":
        # Unsigned range mapping
        val = round(norm * max_val)
    else:
        raise ValueError(f"Unknown encoding: {encoding}")
    # Dynamically calculate hex width based on bits (e.g. 16-bit -> 4 hex char)
    hex_width = (bits + 3) // 4
    return f"0x{val:0{hex_width}X}"


def get_parser():
    """Defines parsing arguments"""
    parser = argparse.ArgumentParser(
        description=__doc__,  # "Set a value to output on DACs on trigger"+__doc__
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--bits", default=16, type=int, help="Resolution in bits (e.g., 8, 12, 16, 24)"
    )
    parser.add_argument("--vmin", default=0.0, type=float, help="Voltage min")
    parser.add_argument("--vmax", default=3.3, type=float, help="Voltage max")
    parser.add_argument(
        "--encoding",
        choices=("offset_binary", "twos_complement"),
        default="offset_binary",
        help="Encoding: twos_complement signed range (-32768 to 32767 for 16-bit) or offset_binary unsigned range (0 to 65535 for 16-bit)",
    )

    parser.add_argument("initial_values", type=str, help="First sample NOWAIT")
    parser.add_argument(
        "triggered_values", type=str, nargs="?", help="First sample after trigger"
    )
    parser.add_argument("uutname", help="UUT hostname")
    return parser


def main(args):
    """Sets up UUT, parses input values and programs the DACs awaiting trigger"""
    uut = acq400_hapi.factory(args.uutname)

    if args.triggered_values:
        # if triggered_values not empty
        uut.s1.low_latency = 0
        uut.s1.dac_enable = 0
        uut.s1.__reset_fifo = 1
        uut.s1.dac_enable = 1
    elif not args.triggered_values and uut.s1.is_triggered == "0":
        # if triggered empty and not triggered
        print("Error: must run with triggered value before clear")
        return

    if args.initial_values:
        initial = is_comma_separated_hexes(args.initial_values)
        if not initial:
            initial = parse_voltages(
                args.initial_values, args.encoding, args.vmin, args.vmax, args.bits
            )
        print(f"Set Initial: {initial}")
        uut.s1.NOIMM_AO_ALL_UNIQUE = initial

    if args.triggered_values:
        triggered = is_comma_separated_hexes(args.triggered_values)
        if not triggered:
            triggered = parse_voltages(
                args.triggered_values, args.encoding, args.vmin, args.vmax, args.bits
            )
        print(f"Set Triggered: {triggered}")
        uut.s1.NOIMM_AO_ALL_UNIQUE = triggered
        print("soft_trigger when ready")


if __name__ == "__main__":
    cli_parser = get_parser()
    cli_arguments = cli_parser.parse_args()
    main(cli_arguments)

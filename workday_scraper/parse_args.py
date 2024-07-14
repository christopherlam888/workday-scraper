import argparse
import sys


def parse_args():
    parser = argparse.ArgumentParser(description="Available Options")
    parser.add_argument("-f", "--file", dest="file", type=str, required=True)
    parser.add_argument(
        "-e",
        "--email",
        dest="email",
        type=str,
        required="-r" in sys.argv
        or "--recipients" in sys.argv
        or "-pw" in sys.argv
        or "--password" in sys.argv,
    )
    parser.add_argument(
        "-pw",
        "--password",
        dest="password",
        type=str,
        required="-e" in sys.argv
        or "--email" in sys.argv
        or "-r" in sys.argv
        or "--recipients" in sys.argv,
    )
    parser.add_argument(
        "-r",
        "--recipients",
        dest="recipients",
        type=str,
        required="-e" in sys.argv
        or "--email" in sys.argv
        or "-pw" in sys.argv
        or "--password" in sys.argv,
    )
    parser.add_argument(
        "-p",
        "--perpetual",
        dest="perpetual",
        action="store_true",
        required="-t" in sys.argv or "--time-period" in sys.argv,
    )
    parser.add_argument(
        "-t",
        "--time-period",
        dest="time-period",
        type=int,
        default=1,
    )
    parser.add_argument("-i", "--initial", dest="initial", action="store_true")
    parser.add_argument("-nj", "--no-json", dest="no-json", action="store_true")
    parser.add_argument("-nr", "--no-rss", dest="no-rss", action="store_true")
    args = vars(parser.parse_args())
    return args

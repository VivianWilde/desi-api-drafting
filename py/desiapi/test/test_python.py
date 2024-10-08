from ..python.api import *
import json


def main():
    client = DesiApiClient(release="fujilite")
    responses = [
        client.get_zcat_radec(210.9, 24.8, 180),
        client.get_zcat_tile(80858, [600, 900, 1000]),
        client.get_zcat_targets([39628368387245557, 39628368404022902]),
    ]
    for i in responses:
        print(i)
        print(i.dtype)
        print()


if __name__ == "__main__":
    main()

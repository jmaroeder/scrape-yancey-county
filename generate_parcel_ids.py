import json

SCROLL_FILENAME = 'scroll2024.json'
PARCEL_IDS_FILENAME = 'parcel_ids.txt'

if __name__ == '__main__':
    with open(SCROLL_FILENAME) as f:
        scroll = json.load(f)

    parcel_ids = set(row['pin'] for row in scroll)

    with open(PARCEL_IDS_FILENAME, 'w') as f:
        f.write('\n'.join(sorted(parcel_ids)) + '\n')

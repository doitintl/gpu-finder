access_entries.append(
    bigquery.AccessEntry("READER", "userByEmail", analyst_group_email)
)
entries = list(dataset.access_entries)
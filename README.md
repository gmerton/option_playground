# Options Playground

```
python3 -m venv .venv
source .venv/bin/activate
pip install pandas pyarrow awswrangler boto3 sqlparse aiohttp polygon-api-client requests pandas-ta
```

List profiles: `aws configure list-profiles`

Select one: `export AWS_PROFILE=clarinut-gmerton`

Run files with code like this:
`PYTHONPATH=src python -m lib.forward.ff`
`PYTHONPATH=src python -m lib.credit_spread.credit_spread_finder`
`PYTHONPATH=src python -m lib.leaps.leap_finder`
`PYTHONPATH=src python -m lib.fly.fly_finder`

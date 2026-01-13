
import sys
import os
import json

# Path hack to reach packages
# Assuming this script is run from project root d:\Documents\Active\StrategyAnalysisPlatform\Main
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), 'packages', 'quant_shared', 'src')))

from quant_shared.models.models import Dataset, MlDatasetSample
from quant_shared.models.connection import get_db, init_db

# Init connection using shared logic
db_gen = get_db()
session = next(db_gen)

datasets = session.query(Dataset).all()
print(f"Found {len(datasets)} datasets.")

for ds in datasets:
    print(f"ID: {ds.dataset_id} | Name: {ds.name}")
    print(f"Features: {ds.feature_config_json}")
    # Inspect one sample to be sure of keys
    sample = session.query(MlDatasetSample).filter_by(dataset_id=ds.dataset_id).first()
    if sample:
        print(f"  Sample Keys: {list(sample.features_json.keys())}")
    print("-" * 30)

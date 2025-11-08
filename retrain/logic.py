from sklearn.model_selection import train_test_split
import pandas as pd


def createDataFrameFromJSON(jsonPath):
    import json

    with open(jsonPath, 'r') as f:
        data = json.load(f)


    df = pd.DataFrame(data["data"])
    return df


def combine(first, second):
    df = createDataFrameFromJSON(first)
    df = pd.concat([df, createDataFrameFromJSON(second)], ignore_index=True)    


    df_train, df_eval = train_test_split(
        df,
        train_size=0.8,
        stratify=df['label'],  # Changed from df.target to df['label']
        random_state=42)
    return df_train, df_eval
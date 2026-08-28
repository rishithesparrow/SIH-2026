import pandas as pd
import numpy as np
from pathlib import Path

# Keep file loading independent of the terminal folder used to start the API.
PROJECT_DIR = Path(__file__).resolve().parent
# The compressed copy is used for browser-based GitHub uploads; pandas reads
# the single-file ZIP directly.  Keep the original CSV as the local fallback.
DATASET_PATH = PROJECT_DIR / "ibtracs.zip"
if not DATASET_PATH.exists():
    DATASET_PATH = PROJECT_DIR / "ibtracs.csv"
data = pd.read_csv(DATASET_PATH, skiprows=[1], low_memory=False)

#print(data.head())
#print(data.columns.tolist()) To know all the columns present
#print(data.shape)

columns = [
    "SID",             # cyclone id
    "SEASON",          # year
    "NAME", 
    "SUBBASIN",           
    "ISO_TIME",        # obsn time
    "LAT",             
    "LON",             
    "WMO_WIND",        
    "WMO_PRES",        
    "NEWDELHI_WIND",  
    "NEWDELHI_PRES",   
    "DIST2LAND",       
    "LANDFALL",        
    "STORM_SPEED",    
    "STORM_DIR",       
    "NATURE"           # type of cyclone system
]

data = data[columns]

data=data[data["SEASON"]>=1990]


# print(data.head())
# print(data.shape)

#print(data.isna().sum())

#print(data.dtypes) not all are float64
#to change to float64
numeric_columns = [
    "WMO_WIND",
    "WMO_PRES",
    "NEWDELHI_WIND",
    "NEWDELHI_PRES",
    "LANDFALL",
    "STORM_SPEED",
    "STORM_DIR"
]

for column in numeric_columns:
    data[column] = pd.to_numeric(data[column], errors="coerce")
#errors are the values that cannot be converted to numbers so by
#errors=coerce we are basically converting to 
#NaN so that we can see the number of missing values

# #Now checking again
# print(data.dtypes)
# print()#so its easier to read its there
# print(data.isna().sum())

# #since we have missing values for wind and pres
# print(data[[
#     "WMO_WIND",
#     "NEWDELHI_WIND",
#     "WMO_PRES",
#     "NEWDELHI_PRES"
# ]].notna().sum())#nontna()is the opposite of isna(), it gives true to values and false to NaN

#to check for inside both in order to get a mixed dataset sicne a lot is missing

# both_wind = (data["WMO_WIND"].notna() & data["NEWDELHI_WIND"].notna())

# only_wmo = (data["WMO_WIND"].notna() & data["NEWDELHI_WIND"].isna()

# only_newdelhi = (data["WMO_WIND"].isna() & data["NEWDELHI_WIND"].notna()

# neither_wind = (data["WMO_WIND"].isna() & data["NEWDELHI_WIND"].isna())


# print("Both:", both_wind.sum())
# print("Only WMO:", only_wmo.sum())
# print("Only New Delhi:", only_newdelhi.sum())
# print("Neither:", neither_wind.sum())


##formation of combined column
data["WIND"]=data["WMO_WIND"].fillna(data["NEWDELHI_WIND"])
# print(data["WIND"].isna().sum())

# #for pressure
# both_pressure = (
#     data["WMO_PRES"].notna() &
#     data["NEWDELHI_PRES"].notna()
# )

# only_wmo_pressure = (data["WMO_PRES"].notna() & data["NEWDELHI_PRES"].isna()

# only_newdelhi_pressure = (data["WMO_PRES"].isna() & data["NEWDELHI_PRES"].notna()

# neither_pressure = (data["WMO_PRES"].isna() & data["NEWDELHI_PRES"].isna()

# print("Both:", both_pressure.sum())
# print("Only WMO:", only_wmo_pressure.sum())
# print("Only New Delhi:", only_newdelhi_pressure.sum())
# print("Neither:", neither_pressure.sum())

#the new column for pressure
data["PRESSURE"]=data["WMO_PRES"].fillna(data["NEWDELHI_PRES"])

# print("Pressure available:", data["PRESSURE"].notna().sum())
# print("Pressure missing:", data["PRESSURE"].isna().sum()) #to check what is there and not there

#for both availability
both_available=(data["WIND"].notna() & data["PRESSURE"].notna())

#print(both_available.sum())#this has only true or false data and sum is being done

usable_data=data[both_available].copy() #what this does is keeps the rows where true is there and gets rid of rows where false is there
#print("Unique cyclones:", usable_data["SID"].nunique()) #.nunique() is so that we can get all the unique cyclonnes in the data

#print(data["SUBBASIN"].value_counts())

ni_data = usable_data[usable_data["SUBBASIN"].isin(["BB", "AS"])].copy()

#print("Usable Bay of Bengal observations:", len(ni_data))
#print("Unique Bay of Bengal cyclones:", ni_data["SID"].nunique())

cyclone_counts = ni_data["SID"].value_counts() #counts the obs for each cyclone

# print("Average observations per cyclone:", cyclone_counts.mean())
# print("Minimum observations:", cyclone_counts.min())
# print("Maximum observations:", cyclone_counts.max())

ni_data = ni_data.copy()  #so that we can safely alter and if there is any wrongdoings we can go back
ni_data["ISO_TIME"]=pd.to_datetime(ni_data["ISO_TIME"], errors="coerce") #to_datetime makes sure than pandas understands that the given string is date and time
# print(ni_data["ISO_TIME"].dtype)
# print(ni_data["ISO_TIME"].isna().sum())
# #if pandas cant convert something to time then itll convvert it to NaT


##Sorting Values

ni_data = ni_data.sort_values(
    by=["SID", "ISO_TIME"]
)

ni_data = ni_data.reset_index(drop=True)#renumbers the data starting from 4400 to 0
#drop=true means dont keep the index as another column

# print(
#     ni_data[
#         ["SID", "ISO_TIME", "LAT", "LON"]
#     ].head(15)
# )


##next .groupby used to group cyclones by SID.. 
##["any_column"].shift(-1) used to shift the data up and then assign it to another column for example
##similarly for instead of -1, we can put another number and accordingly shift and get another column as we wish
##using them

ni_data["NEXT_LAT"] = (ni_data.groupby("SID")["LAT"].shift(-1))
ni_data["NEXT_LON"] = (ni_data.groupby("SID")["LON"].shift(-1))
ni_data["NEXT_WIND"] = (ni_data.groupby("SID")["WIND"].shift(-1))
ni_data["NEXT_PRESSURE"] = (ni_data.groupby("SID")["PRESSURE"].shift(-1))
ni_data["PREV_LAT"] = (ni_data.groupby("SID")["LAT"].shift(1))
ni_data["PREV_LON"] = (ni_data.groupby("SID")["LON"].shift(1))
ni_data["LAT_CHANGE"] = (ni_data["LAT"] - ni_data["PREV_LAT"])
ni_data["LON_CHANGE"] = (ni_data["LON"] - ni_data["PREV_LON"])
ni_data["PREV_TIME"] = (ni_data.groupby("SID")["ISO_TIME"].shift(1))
ni_data["TIME_DIFF"] = (ni_data["ISO_TIME"] - ni_data["PREV_TIME"])
ni_data["TIME_DIFF_HOURS"] = (ni_data["TIME_DIFF"].dt.total_seconds() / 3600)  #dt.total_seconds then divide by 3600 to convert the vaues intoo numercial inputs since sgboost wants numerical inputs
ni_data["NEXT_TIME"] = (ni_data.groupby("SID")["ISO_TIME"].shift(-1))
ni_data["NEXT_TIME_DIFF"] = (ni_data["NEXT_TIME"] - ni_data["ISO_TIME"])
ni_data["NEXT_TIME_DIFF_HOURS"] = (ni_data["NEXT_TIME_DIFF"].dt.total_seconds() / 3600)
ni_data["PREV_TIME_DIFF_HOURS"] = (ni_data.groupby("SID")["TIME_DIFF_HOURS"].shift(1))

# print(
#     ni_data["NEXT_TIME_DIFF_HOURS"]
#     .value_counts()
#     .sort_index()
# )




# print(
#     ni_data["TIME_DIFF_HOURS"]
#     .value_counts()               #check for time differnces and how many there are and accordingly well 
#     .sort_index()                 #have to strain them. getting overwhelming 3 hr diff with some 15h 0.5 1.0 etc
# )
##RESULT
# NEXT_TIME_DIFF_HOURS
# 0.5        1
# 1.0        2
# 2.0        2
# 2.5        1
# 3.0     7904
# 6.0        6
# 15.0      58
# 45.0       1

# print("Observations:", len(ni_data))
# print("Unique cyclones:", ni_data["SID"].nunique())
# print(ni_data["SUBBASIN"].value_counts())


# print("ML observations:", len(ml_data))
# print("ML cyclones:", ml_data["SID"].nunique())
# print(ml_data["SUBBASIN"].value_counts())

####Final dataset is ml_data

ni_data["PREV_WIND"] = (
    ni_data.groupby("SID")["WIND"].shift(1)
)

ni_data["PREV_PRESSURE"] = (
    ni_data.groupby("SID")["PRESSURE"].shift(1)
)
ni_data["WIND_CHANGE"] = (
    ni_data["WIND"] - ni_data["PREV_WIND"]
)

ni_data["PRESSURE_CHANGE"] = (
    ni_data["PRESSURE"] - ni_data["PREV_PRESSURE"]
)

ni_data["PREV_LAT_CHANGE"] = (
    ni_data.groupby("SID")["LAT_CHANGE"].shift(1)
)

ni_data["PREV_LON_CHANGE"] = (
    ni_data.groupby("SID")["LON_CHANGE"].shift(1)
)

ni_data["PREV_WIND_CHANGE"] = (
    ni_data.groupby("SID")["WIND_CHANGE"].shift(1)
)

ni_data["PREV_PRESSURE_CHANGE"] = (
    ni_data.groupby("SID")["PRESSURE_CHANGE"].shift(1)
)

#####Using this data gave worse results for some reason, noise prob
ni_data["LAT_CHANGE_CHANGE"] = (
    ni_data["LAT_CHANGE"]
    - ni_data["PREV_LAT_CHANGE"]
)

ni_data["LON_CHANGE_CHANGE"] = (
    ni_data["LON_CHANGE"]
    - ni_data["PREV_LON_CHANGE"]
)

ni_data["WIND_CHANGE_CHANGE"] = (
    ni_data["WIND_CHANGE"]
    - ni_data["PREV_WIND_CHANGE"]
)

ni_data["PRESSURE_CHANGE_CHANGE"] = (
    ni_data["PRESSURE_CHANGE"]
    - ni_data["PREV_PRESSURE_CHANGE"]
)

ml_data = ni_data[
    (ni_data["PREV_TIME_DIFF_HOURS"] == 3) &
    (ni_data["TIME_DIFF_HOURS"] == 3) &
    (ni_data["NEXT_TIME_DIFF_HOURS"] == 3)
].copy() #this ensures the changes have occured in ml data too

# print(
#     ml_data[
#         [
#             "WIND",
#             "PREV_WIND",
#             "WIND_CHANGE",
#             "PRESSURE",
#             "PREV_PRESSURE",
#             "PRESSURE_CHANGE"
#         ]
#     ].head(10)
# )

# print("Mean wind:", ml_data["WIND"].mean())
# print("Median wind:", ml_data["WIND"].median())
# print("Minimum wind:", ml_data["WIND"].min())
# print("Maximum wind:", ml_data["WIND"].max())


###enhacing the data so that it gives more accurate results

# print(ml_data["ISO_TIME"].head(20))
# print("Earliest:", ml_data["ISO_TIME"].min())
# print("Latest:", ml_data["ISO_TIME"].max())

# unique_dates = (
#     ml_data["ISO_TIME"]
#     .dt.normalize()
#     .drop_duplicates()
#     .sort_values()
# )

# print("Unique dates:", len(unique_dates))
# print(unique_dates.head())
# print(unique_dates.tail())



####enhancement of dataset to be done after if selected for 2nd round
# import cdsapi

# client = cdsapi.Client()

# print("CDS API connection successful")

# dates_1990 = (
#     ml_data.loc[
#         ml_data["ISO_TIME"].dt.year == 1990,
#         "ISO_TIME"
#     ]
#     .dt.date
#     .drop_duplicates()
# )

# print(dates_1990.to_list())






###test train split
# the whole block separates cyclone data into a training set 
# and a testing set without letting the same 
# cyclone appear in both.
########################
from sklearn.model_selection import GroupShuffleSplit  #groupshufflesplit makes sure that every sid is used as one group

features = [
    "LAT",
    "LON",

    "PREV_LAT",
    "PREV_LON",

    "LAT_CHANGE",
    "LON_CHANGE",

    "LAT_CHANGE_CHANGE",
    "LON_CHANGE_CHANGE",

    "WIND",
    "PREV_WIND",
    "WIND_CHANGE",
    "WIND_CHANGE_CHANGE",

    "PRESSURE",
    "PREV_PRESSURE",
    "PRESSURE_CHANGE",
    "PRESSURE_CHANGE_CHANGE",

    "STORM_SPEED",
    "STORM_DIR"
]

X = ml_data[features]   #X=input data


ml_data["NEXT_LAT_CHANGE"] = (
    ml_data["NEXT_LAT"] - ml_data["LAT"]
)

ml_data["NEXT_LON_CHANGE"] = (
    ml_data["NEXT_LON"] - ml_data["LON"]
)

ml_data["NEXT_WIND_CHANGE"] = (
    ml_data["NEXT_WIND"] - ml_data["WIND"]
)

ml_data["NEXT_PRESSURE_CHANGE"] = (
    ml_data["NEXT_PRESSURE"] - ml_data["PRESSURE"]
)
y_lat = ml_data["NEXT_LAT_CHANGE"]
y_lon = ml_data["NEXT_LON_CHANGE"]
y_wind = ml_data["NEXT_WIND_CHANGE"]
y_pressure = ml_data["NEXT_PRESSURE_CHANGE"]
##the prediction that needs to be predicted
##is y and X is the input data

groups = ml_data["SID"]


#for splitting
splitter = GroupShuffleSplit(
    n_splits=1,     #means we want to make only one train?test split
    test_size=0.2,  #means put 20% in to testing and 80% into training
    random_state=42 #makes the random split repeatable, maybe in the future we can get rid of this
)                   #basically randomstate is the seed like in minecraft

train_idx, test_idx = next(    ##for deciding which part or row that is goes to tseting or training
    splitter.split(
        X,
        groups=groups
    )
)

#test datasets
X_train = X.iloc[train_idx]  ##.iloc means select rows by their numerical positions for eg if train_idx has 0,2,5 as the rows then it selects those rows to train on
X_test = X.iloc[test_idx]

y_lat_train = y_lat.iloc[train_idx]
y_lat_test = y_lat.iloc[test_idx]

y_lon_train = y_lon.iloc[train_idx]
y_lon_test = y_lon.iloc[test_idx]

y_wind_train = y_wind.iloc[train_idx]
y_wind_test = y_wind.iloc[test_idx]

y_pressure_train = y_pressure.iloc[train_idx]
y_pressure_test = y_pressure.iloc[test_idx]
########################
 
# print("Training rows:", len(X_train))
# print("Testing rows:", len(X_test))

# print(
#     "Training cyclones:",
#     ml_data.iloc[train_idx]["SID"].nunique()
# )

# print(
#     "Testing cyclones:",
#     ml_data.iloc[test_idx]["SID"].nunique()
# )


from catboost import CatBoostRegressor

lat_model = CatBoostRegressor(
    iterations=500,          ### hyperparameters for XGboost
    depth=6,                 #colsample_bytree=0.8 means each tree gets random 80% of the imput features, coluumns that is
    learning_rate=0.05,      
    loss_function="RMSE",     #n_est=300 means 300 decision tress ####decisiion tress are boolean in nature. have true or false as result that is
                              #learning rate is how strongly each new tree corrects the mistakes of the old trees. smaller value makes learning slower but more cautious
    random_seed=42,          #subsample 0.8 means 80 % of the training set being used (rows tot 5583 out of which 4466 are used for training)
    verbose=False
)

lon_model = CatBoostRegressor(
    iterations=500,
    depth=6,                       #RMSE is root mean squared error, which the regression model needs to minimize
    learning_rate=0.05,            #verbose basicaly gives us training info about how much or uptil how much it has trained, for example if verbose=50, then after every 50 interations itll tell that 50 iterations have been trained on
    loss_function="RMSE",
    random_seed=42,
    verbose=False
)

wind_model = CatBoostRegressor(
    iterations=500,
    depth=6,
    learning_rate=0.05,
    loss_function="RMSE",
    random_seed=42,
    verbose=False
)

pressure_model = CatBoostRegressor(
    iterations=500,
    depth=6,
    learning_rate=0.05,
    loss_function="RMSE",
    random_seed=42,
    verbose=False
)

##training
lat_model.fit(     #.fit() means train the model
    X_train,
    y_lat_train
)

lon_model.fit(
    X_train,
    y_lon_train
)

wind_model.fit(
    X_train,
    y_wind_train
)

pressure_model.fit(
    X_train,
    y_pressure_train
)

##prediction
pred_lat_change = lat_model.predict(X_test)

pred_lon_change = lon_model.predict(X_test)

pred_lat = ( X_test["LAT"].to_numpy() + pred_lat_change)

pred_lon = ( X_test["LON"].to_numpy()+ pred_lon_change)

pred_wind_change = wind_model.predict(X_test)

pred_pressure_change = pressure_model.predict(X_test)

pred_wind = (
    X_test["WIND"].to_numpy()
    + pred_wind_change
)

pred_pressure = (
    X_test["PRESSURE"].to_numpy()
    + pred_pressure_change
)


# print("Predicted LAT:", pred_lat[:10])
# print("Actual LAT:", y_lat_test.iloc[:10].values)

# print()

# print("Predicted LON:", pred_lon[:10])
# print("Actual LON:", y_lon_test.iloc[:10].values)  ##.values removes the Pandas labels/indexes and gives just the numerical values, sothe output is easier to compare.

#####for conversion from lat and lon to distance in km

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)  
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        +
        np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    c = 2 * np.arctan2(
        np.sqrt(a),
        np.sqrt(1 - a)
    )

    return R * c


actual_lat = (
    ml_data.iloc[test_idx]["NEXT_LAT"]
    .to_numpy()
)

actual_lon = (
    ml_data.iloc[test_idx]["NEXT_LON"]
    .to_numpy()
)

track_errors = haversine(
    actual_lat,
    actual_lon,
    pred_lat,
    pred_lon
)

actual_wind = (
    ml_data.iloc[test_idx]["NEXT_WIND"]
    .to_numpy()
)

actual_pressure = (
    ml_data.iloc[test_idx]["NEXT_PRESSURE"]
    .to_numpy()
)

wind_errors = np.abs(
    actual_wind - pred_wind
)

pressure_errors = np.abs(
    actual_pressure - pred_pressure
)

# print("Wind mean error:", wind_errors.mean(), "kt")
# print("Wind median error:", np.median(wind_errors), "kt")
# print("Wind max error:", wind_errors.max(), "kt")
# print()
# print("Pressure mean error:", pressure_errors.mean(), "hPa")
# print("Pressure median error:", np.median(pressure_errors), "hPa")
# print("Pressure max error:", pressure_errors.max(), "hPa")
# print()
# print("Mean track error:", track_errors.mean(), "km")
# print("Median track error:", np.median(track_errors), "km")
# print("Minimum track error:", track_errors.min(), "km")
# print("Maximum track error:", track_errors.max(), "km")
# print("First 10 errors:", track_errors[:10])
# print()



################checking if the model is truly adding to preds
# persistence_lat = X_test["LAT"] + X_test["LAT_CHANGE"]

# persistence_lon = X_test["LON"] + X_test["LON_CHANGE"]

# persistence_errors = haversine(
#     actual_lat,
#     actual_lon,
#     persistence_lat.to_numpy(),
#     persistence_lon.to_numpy()
# )

# print("Persistence mean error:", persistence_errors.mean(), "km")
# print("Persistence median error:", np.median(persistence_errors), "km")
# print("Persistence max error:", persistence_errors.max(), "km")

# print()
# print("CatBoost mean error:", track_errors.mean(), "km")
# print("CatBoost median error:", np.median(track_errors), "km")
# print("CatBoost max error:", track_errors.max(), "km")
###############



############For storm speed and direction
def calculate_speed_direction(
    lat1,
    lon1,
    lat2,
    lon2,
    hours=3
):

    distance_km = haversine(
        lat1,
        lon1,
        lat2,
        lon2
    )

    speed_kmh = distance_km / hours

    #km/h to knots
    speed_knots = speed_kmh / 1.852


    # cood to radians
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)

    dlon_rad = np.radians(
        lon2 - lon1
    )


    # Calculate bearing
    x = (
        np.sin(dlon_rad)
        * np.cos(lat2_rad)
    )

    y = (
        np.cos(lat1_rad)
        * np.sin(lat2_rad)
        -
        np.sin(lat1_rad)
        * np.cos(lat2_rad)
        * np.cos(dlon_rad)
    )

    direction = (
        np.degrees(
            np.arctan2(x, y)
        )
        + 360
    ) % 360


    return speed_knots, direction
################


################


####multiple steps predictor
def predict_next_state(current, previous):

    row = {
        "LAT": current["LAT"],
    "LON": current["LON"],

    "PREV_LAT": previous["LAT"],
    "PREV_LON": previous["LON"],

    "LAT_CHANGE": current["LAT_CHANGE"],
    "LON_CHANGE": current["LON_CHANGE"],

    "LAT_CHANGE_CHANGE": (
        current["LAT_CHANGE"]
        - previous["LAT_CHANGE"]
    ),

    "LON_CHANGE_CHANGE": (
        current["LON_CHANGE"]
        - previous["LON_CHANGE"]
    ),

    "WIND": current["WIND"],
    "PREV_WIND": previous["WIND"],

    "WIND_CHANGE": current["WIND_CHANGE"],

    "WIND_CHANGE_CHANGE": (
        current["WIND_CHANGE"]
        - previous["WIND_CHANGE"]
    ),

    "PRESSURE": current["PRESSURE"],
    "PREV_PRESSURE": previous["PRESSURE"],

    "PRESSURE_CHANGE": current["PRESSURE_CHANGE"],

    "PRESSURE_CHANGE_CHANGE": (
        current["PRESSURE_CHANGE"]
        - previous["PRESSURE_CHANGE"]
        ),

        "STORM_SPEED": current["STORM_SPEED"],
        "STORM_DIR": current["STORM_DIR"]
    }

    row_df = pd.DataFrame([row])

    lat_change = lat_model.predict(
        row_df[features]
    )[0]

    lon_change = lon_model.predict(
        row_df[features]
    )[0]

    wind_change = wind_model.predict(
        row_df[features]
    )[0]

    pressure_change = pressure_model.predict(
        row_df[features]
    )[0]

    next_lat = (
    current["LAT"]
    + lat_change
    )

    next_lon = (
    current["LON"]
    + lon_change
    ) 

    next_speed, next_direction = (
    calculate_speed_direction(
        current["LAT"],
        current["LON"],
        next_lat,
        next_lon,
        hours=3
    )
)

    next_state = {
    
    "LAT": next_lat,
    "LON": next_lon,

    "LAT_CHANGE": lat_change,
    "LON_CHANGE": lon_change,

    "WIND": (
        current["WIND"]
        + wind_change
    ),

    "WIND_CHANGE": wind_change,

    "PRESSURE": (
        current["PRESSURE"]
        + pressure_change
    ),

    "PRESSURE_CHANGE": pressure_change,

    "STORM_SPEED": next_speed,
    "STORM_DIR": next_direction
}
    

    return next_state


##The loop
def forecast_cyclone(previous, current, steps=8):

    forecast = []

    for step in range(steps):

        next_state = predict_next_state( current, previous)

        # Store how far into the future this predictionn is
        next_state["FORECAST_HOUR"] = (
            (step + 1) * 3
        )

        forecast.append(next_state)

        # Shift forward one step
        previous = current
        current = next_state

    return pd.DataFrame(forecast)


####################

########test run for loop
#Picking a cyclone from the test set
test_sids = ml_data.iloc[test_idx]["SID"].unique()

test_sid = test_sids[0]

cyclone = ni_data[
    ni_data["SID"] == test_sid
].sort_values("ISO_TIME")

# print(
#     cyclone[
#         [
#             "SID",
#             "NAME",
#             "ISO_TIME",
#             "LAT",
#             "LON",
#             "WIND",
#             "PRESSURE"
#         ]
#     ].head(10)
# )
#############

previous_row = cyclone.iloc[1]
current_row = cyclone.iloc[2]

previous = {
    "LAT": previous_row["LAT"],
    "LON": previous_row["LON"],

    "LAT_CHANGE": previous_row["LAT_CHANGE"],
    "LON_CHANGE": previous_row["LON_CHANGE"],

    "WIND": previous_row["WIND"],
    "WIND_CHANGE": previous_row["WIND_CHANGE"],

    "PRESSURE": previous_row["PRESSURE"],
    "PRESSURE_CHANGE": previous_row["PRESSURE_CHANGE"],

    "STORM_SPEED": previous_row["STORM_SPEED"],
    "STORM_DIR": previous_row["STORM_DIR"]
}

current = {
    "LAT": current_row["LAT"],
    "LON": current_row["LON"],

    "LAT_CHANGE": current_row["LAT_CHANGE"],
    "LON_CHANGE": current_row["LON_CHANGE"],

    "WIND": current_row["WIND"],
    "WIND_CHANGE": current_row["WIND_CHANGE"],

    "PRESSURE": current_row["PRESSURE"],
    "PRESSURE_CHANGE": current_row["PRESSURE_CHANGE"],

    "STORM_SPEED": current_row["STORM_SPEED"],
    "STORM_DIR": current_row["STORM_DIR"]
}

forecast_12h = forecast_cyclone(
    previous,
    current,
    steps=4
)

#print(forecast_12h)

#####check for error in forecast
# Actual observations corresponding to the forecast
actual_future = cyclone.iloc[3:7].copy()

# Make sure we compare only the number of rows available
compare_length = min(
    len(forecast_12h),
    len(actual_future)
)

forecast_compare = forecast_12h.iloc[
    :compare_length
].copy()

actual_compare = actual_future.iloc[
    :compare_length
].copy()


# Calculate track error for every forecast step
multi_step_errors = haversine(
    actual_compare["LAT"].to_numpy(),
    actual_compare["LON"].to_numpy(),
    forecast_compare["LAT"].to_numpy(),
    forecast_compare["LON"].to_numpy()
)


# Calculate wind and pressure errors
multi_wind_errors = np.abs(
    actual_compare["WIND"].to_numpy()
    -
    forecast_compare["WIND"].to_numpy()
)

multi_pressure_errors = np.abs(
    actual_compare["PRESSURE"].to_numpy()
    -
    forecast_compare["PRESSURE"].to_numpy()
)


# Build comparison table
comparison = pd.DataFrame({
    "FORECAST_HOUR":
        forecast_compare["FORECAST_HOUR"].to_numpy(),

    "ACTUAL_LAT":
        actual_compare["LAT"].to_numpy(),

    "PRED_LAT":
        forecast_compare["LAT"].to_numpy(),

    "ACTUAL_LON":
        actual_compare["LON"].to_numpy(),

    "PRED_LON":
        forecast_compare["LON"].to_numpy(),

    "TRACK_ERROR_KM":
        multi_step_errors,

    "ACTUAL_WIND":
        actual_compare["WIND"].to_numpy(),

    "PRED_WIND":
        forecast_compare["WIND"].to_numpy(),

    "WIND_ERROR_KT":
        multi_wind_errors,

    "ACTUAL_PRESSURE":
        actual_compare["PRESSURE"].to_numpy(),

    "PRED_PRESSURE":
        forecast_compare["PRESSURE"].to_numpy(),

    "PRESSURE_ERROR_HPA":
        multi_pressure_errors
})

pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)
# print()
# print(comparison)

######## AI PART
######
# =========================================================
# MULTI-CYCLONE RECURSIVE FORECAST TEST
# =========================================================

recursive_results = []

test_sids = ml_data.iloc[test_idx]["SID"].unique()

steps = 4    


for sid in test_sids:

    cyclone_test = (
        ni_data[
            ni_data["SID"] == sid
        ]
        .sort_values("ISO_TIME")
        .reset_index(drop=True)
    )

    # We need:
    # t-6h, t-3h, current time
    # plus 8 future observations
    if len(cyclone_test) < 11:
        continue


    # -----------------------------------------------------
    # Find a valid starting point
    # -----------------------------------------------------

    valid_start = None

    for i in range(
        2,
        len(cyclone_test) - steps
    ):

        # We need everything from:
        # i-2  -> enough history for change-change
        # i+8  -> enough future data for evaluation
        time_section = cyclone_test.iloc[
            i - 2 : i + steps + 1
        ]["ISO_TIME"]

        gaps = (
            time_section
            .diff()
            .dt.total_seconds()
            .div(3600)
            .dropna()
        )

        # Every observation must be exactly 3 hours apart
        if (gaps == 3).all():
            valid_start = i
            break


    # No usable 24-hour continuous section
    if valid_start is None:
        continue


    i = valid_start

    previous_row = cyclone_test.iloc[i - 1]
    current_row = cyclone_test.iloc[i]


    # -----------------------------------------------------
    # Create starting states
    # -----------------------------------------------------

    previous = {
        "LAT": previous_row["LAT"],
        "LON": previous_row["LON"],

        "LAT_CHANGE": previous_row["LAT_CHANGE"],
        "LON_CHANGE": previous_row["LON_CHANGE"],

        "WIND": previous_row["WIND"],
        "WIND_CHANGE": previous_row["WIND_CHANGE"],

        "PRESSURE": previous_row["PRESSURE"],
        "PRESSURE_CHANGE":
            previous_row["PRESSURE_CHANGE"],

        "STORM_SPEED": previous_row["STORM_SPEED"],
        "STORM_DIR": previous_row["STORM_DIR"]
    }


    current = {
        "LAT": current_row["LAT"],
        "LON": current_row["LON"],

        "LAT_CHANGE": current_row["LAT_CHANGE"],
        "LON_CHANGE": current_row["LON_CHANGE"],

        "WIND": current_row["WIND"],
        "WIND_CHANGE": current_row["WIND_CHANGE"],

        "PRESSURE": current_row["PRESSURE"],
        "PRESSURE_CHANGE":
            current_row["PRESSURE_CHANGE"],

        "STORM_SPEED": current_row["STORM_SPEED"],
        "STORM_DIR": current_row["STORM_DIR"]
    }


    # -----------------------------------------------------
    # Produce recursive 24-hour forecast
    # -----------------------------------------------------

    forecast = forecast_cyclone(
        previous,
        current,
        steps=steps
    )


    # Actual future observations
    actual = cyclone_test.iloc[
        i + 1 : i + steps + 1
    ]


    # -----------------------------------------------------
    # Calculate track errors
    # -----------------------------------------------------

    track_error = haversine(
        actual["LAT"].to_numpy(),
        actual["LON"].to_numpy(),

        forecast["LAT"].to_numpy(),
        forecast["LON"].to_numpy()
    )


    # Wind error
    wind_error = np.abs(
        actual["WIND"].to_numpy()
        -
        forecast["WIND"].to_numpy()
    )


    # Pressure error
    pressure_error = np.abs(
        actual["PRESSURE"].to_numpy()
        -
        forecast["PRESSURE"].to_numpy()
    )


    # -----------------------------------------------------
    # Save each forecast horizon
    # -----------------------------------------------------

    for j in range(steps):

        recursive_results.append({

            "SID": sid,

            "FORECAST_HOUR":
                (j + 1) * 3,

            "TRACK_ERROR_KM":
                track_error[j],

            "WIND_ERROR_KT":
                wind_error[j],

            "PRESSURE_ERROR_HPA":
                pressure_error[j]
        })

recursive_results = pd.DataFrame(
    recursive_results
)


print()
print(
    "Cyclones evaluated:",
    recursive_results["SID"].nunique()
)


horizon_results = (
    recursive_results
    .groupby("FORECAST_HOUR")
    .agg(

        TRACK_MEAN=(
            "TRACK_ERROR_KM",
            "mean"
        ),

        TRACK_MEDIAN=(
            "TRACK_ERROR_KM",
            "median"
        ),

        TRACK_MAX=(
            "TRACK_ERROR_KM",
            "max"
        ),

        WIND_MEAN=(
            "WIND_ERROR_KT",
            "mean"
        ),

        PRESSURE_MEAN=(
            "PRESSURE_ERROR_HPA",
            "mean"
        ),

        COUNT=(
            "SID",
            "count"
        )
    )
)


print()
print("Recursive forecast performance:")
print(horizon_results)

########start of not me and complete AI
# =========================================================
# FLASK API FOR THE SIH DIGITAL-TWIN FRONTEND
# =========================================================
# This section exposes the existing trained CatBoost models and IBTrACS
# archive to a frontend.  The model features and recursive prediction logic
# above are deliberately unchanged.

import os
import time
from datetime import timedelta
from urllib.error import URLError

from flask import Flask, jsonify, make_response, request


app = Flask(__name__)

# Fallback values from the previously measured CHANGE_CHANGE recursive test.
# They are only used if a particular horizon cannot be evaluated.  Normal API
# runs use the fresh TRACK_MEAN values calculated in `horizon_results` above.
FALLBACK_UNCERTAINTY_BY_HOUR_KM = {
    3: 6.0,
    6: 18.0,
    9: 36.0,
    12: 60.0,
}


def build_uncertainty_from_measured_errors(metrics):
    """
    Use the model's current mean recursive track error as the uncertainty
    radius for every supported forecast horizon.  TRACK_MEAN is calculated
    above from unseen cyclone SIDs, so this is not a median or a hard-coded
    display value.
    """
    uncertainty = FALLBACK_UNCERTAINTY_BY_HOUR_KM.copy()

    for forecast_hour in uncertainty:
        if forecast_hour not in metrics.index:
            continue

        track_mean = metrics.loc[forecast_hour, "TRACK_MEAN"]
        if pd.notna(track_mean) and np.isfinite(float(track_mean)) and float(track_mean) >= 0:
            uncertainty[forecast_hour] = float(track_mean)

    return uncertainty


# The map uncertainty corridor now follows the latest model evaluation rather
# than a manually maintained set of values.
UNCERTAINTY_BY_HOUR_KM = build_uncertainty_from_measured_errors(horizon_results)

SIMULATION_NOTICE = (
    "Model-generated/hypothetical simulation. This is not an official "
    "meteorological forecast or warning."
)
HISTORICAL_NOTICE = "Historical IBTrACS observations; these are not predictions."
# No separate disclaimer text is returned for the settlement-risk panel.
RISK_NOTICE = ""


# CORS allows the separately hosted frontend to call this local API during
# development.  Restrict this to the deployed frontend domain before a public
# deployment.
@app.before_request
def answer_cors_preflight():
    if request.method == "OPTIONS":
        return make_response("", 204)
    return None


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ---- Small API helpers -------------------------------------------------
# These helpers keep validation and JSON formatting in one place, so the
# endpoint functions below remain focused on one job each.

_MISSING = object()


def _read_number(values, possible_keys, default=_MISSING):
    """Read a finite numeric value while accepting frontend-friendly names."""
    for key in possible_keys:
        if key in values and values[key] not in (None, ""):
            try:
                value = float(values[key])
            except (TypeError, ValueError) as error:
                raise ValueError(f"'{key}' must be a number.") from error
            if not np.isfinite(value):
                raise ValueError(f"'{key}' must be a finite number.")
            return value

    if default is not _MISSING:
        return default
    readable_name = possible_keys[-1]
    raise ValueError(f"Missing required numeric field '{readable_name}'.")


def _read_text(values, possible_keys, default=None):
    for key in possible_keys:
        if key in values and values[key] not in (None, ""):
            return str(values[key]).strip()
    return default


def _rounded(value, digits=4):
    """Convert NumPy/Pandas numeric values into safe, readable JSON numbers."""
    if value is None or pd.isna(value) or not np.isfinite(float(value)):
        return None
    return round(float(value), digits)


def _api_error(message, status_code=400):
    return jsonify({"error": message}), status_code


def _request_json_object():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValueError("Send a JSON object in the request body.")
    return body


# Simulator input helper: converts a user-entered speed and travel bearing
# into the 3-hour coordinate movement expected by the trained model. Bearing
# follows normal map convention: 0° = north, 90° = east, 180° = south,
# 270° = west.
def calculate_movement_from_speed_direction(
    lat,
    lon,
    speed_knots,
    direction_degrees,
    hours=3,
):
    """Return LAT_CHANGE and LON_CHANGE for the supplied movement period."""
    earth_radius_km = 6371.0
    distance_km = speed_knots * 1.852 * hours
    angular_distance = distance_km / earth_radius_km
    bearing = np.radians(direction_degrees)
    start_lat = np.radians(lat)
    start_lon = np.radians(lon)

    end_lat = np.arcsin(
        np.sin(start_lat) * np.cos(angular_distance)
        + np.cos(start_lat) * np.sin(angular_distance) * np.cos(bearing)
    )
    end_lon = start_lon + np.arctan2(
        np.sin(bearing) * np.sin(angular_distance) * np.cos(start_lat),
        np.cos(angular_distance) - np.sin(start_lat) * np.sin(end_lat),
    )

    end_lat_degrees = np.degrees(end_lat)
    end_lon_degrees = (np.degrees(end_lon) + 540) % 360 - 180
    return end_lat_degrees - lat, end_lon_degrees - lon


def _build_start_states(payload):
    """
    Build the two states needed by the unchanged recursive model.

    A frontend can send complete `previous` and `current` state objects. For
    a manual simulation it can instead send current lat/lon/wind/pressure plus
    stormSpeed and stormDirection; this function derives the 3-hour movement
    features needed by the model. Selecting a historical point remains useful
    because it supplies real preceding movement information.
    """
    current_input = payload.get("current", payload)
    previous_input = payload.get("previous", {})
    if not isinstance(current_input, dict) or not isinstance(previous_input, dict):
        raise ValueError("'current' and 'previous' must be JSON objects.")

    current_lat = _read_number(current_input, ("LAT", "lat", "latitude"))
    current_lon = _read_number(current_input, ("LON", "lon", "longitude"))
    current_wind = _read_number(current_input, ("WIND", "wind"))
    current_pressure = _read_number(current_input, ("PRESSURE", "pressure"))
    if not -90 <= current_lat <= 90 or not -180 <= current_lon <= 180:
        raise ValueError("Latitude must be between -90 and 90; longitude must be between -180 and 180.")
    if current_wind < 0 or current_pressure <= 0:
        raise ValueError("'wind' must be non-negative and 'pressure' must be greater than zero.")

    supplied_previous_lat = _read_number(
        previous_input, ("LAT", "lat", "latitude"), default=None
    )
    supplied_previous_lon = _read_number(
        previous_input, ("LON", "lon", "longitude"), default=None
    )
    supplied_previous_wind = _read_number(previous_input, ("WIND", "wind"), default=None)
    supplied_previous_pressure = _read_number(
        previous_input, ("PRESSURE", "pressure"), default=None
    )

    # Select one movement source in order of reliability. Manual coordinate
    # changes have priority; otherwise convert speed + bearing for a simple
    # simulator form. A historical prior position is the final option.
    supplied_lat_change = _read_number(
        current_input, ("LAT_CHANGE", "latChange", "lat_change"), default=None
    )
    supplied_lon_change = _read_number(
        current_input, ("LON_CHANGE", "lonChange", "lon_change"), default=None
    )
    supplied_storm_speed = _read_number(
        current_input, ("STORM_SPEED", "stormSpeed", "storm_speed"), default=None
    )
    supplied_storm_direction = _read_number(
        current_input, ("STORM_DIR", "stormDirection", "storm_dir"), default=None
    )

    if (supplied_lat_change is None) != (supplied_lon_change is None):
        raise ValueError("Provide both 'latChange' and 'lonChange', or neither.")
    if (supplied_storm_speed is None) != (supplied_storm_direction is None):
        raise ValueError("Provide both 'stormSpeed' and 'stormDirection', or neither.")
    if (supplied_previous_lat is None) != (supplied_previous_lon is None):
        raise ValueError("Provide both previous 'lat' and 'lon', or neither.")

    if supplied_lat_change is not None:
        current_lat_change = supplied_lat_change
        current_lon_change = supplied_lon_change
        movement_source = "manual coordinate movement"
    elif supplied_storm_speed is not None:
        if supplied_storm_speed < 0 or not 0 <= supplied_storm_direction <= 360:
            raise ValueError("'stormSpeed' must be non-negative and 'stormDirection' must be from 0 to 360 degrees.")
        current_lat_change, current_lon_change = calculate_movement_from_speed_direction(
            current_lat,
            current_lon,
            supplied_storm_speed,
            supplied_storm_direction,
            hours=3,
        )
        movement_source = "storm speed and direction"
    elif supplied_previous_lat is not None:
        current_lat_change = current_lat - supplied_previous_lat
        current_lon_change = current_lon - supplied_previous_lon
        movement_source = "previous position"
    else:
        current_lat_change = 0.0
        current_lon_change = 0.0
        movement_source = "no movement supplied (stationary starting assumption)"

    current_wind_change = _read_number(
        current_input, ("WIND_CHANGE", "windChange", "wind_change"),
        default=(current_wind - supplied_previous_wind)
        if supplied_previous_wind is not None else 0.0,
    )
    current_pressure_change = _read_number(
        current_input, ("PRESSURE_CHANGE", "pressureChange", "pressure_change"),
        default=(current_pressure - supplied_previous_pressure)
        if supplied_previous_pressure is not None else 0.0,
    )

    previous = {
        "LAT": supplied_previous_lat
        if supplied_previous_lat is not None else current_lat - current_lat_change,
        "LON": supplied_previous_lon
        if supplied_previous_lon is not None else current_lon - current_lon_change,
        "WIND": supplied_previous_wind
        if supplied_previous_wind is not None else current_wind - current_wind_change,
        "PRESSURE": supplied_previous_pressure
        if supplied_previous_pressure is not None else current_pressure - current_pressure_change,
        "LAT_CHANGE": _read_number(
            previous_input, ("LAT_CHANGE", "latChange", "lat_change"), default=0.0
        ),
        "LON_CHANGE": _read_number(
            previous_input, ("LON_CHANGE", "lonChange", "lon_change"), default=0.0
        ),
        "WIND_CHANGE": _read_number(
            previous_input, ("WIND_CHANGE", "windChange", "wind_change"), default=0.0
        ),
        "PRESSURE_CHANGE": _read_number(
            previous_input,
            ("PRESSURE_CHANGE", "pressureChange", "pressure_change"),
            default=0.0,
        ),
    }

    calculated_speed, calculated_direction = calculate_speed_direction(
        previous["LAT"], previous["LON"], current_lat, current_lon, hours=3
    )
    current = {
        "LAT": current_lat,
        "LON": current_lon,
        "WIND": current_wind,
        "PRESSURE": current_pressure,
        "LAT_CHANGE": current_lat_change,
        "LON_CHANGE": current_lon_change,
        "WIND_CHANGE": current_wind_change,
        "PRESSURE_CHANGE": current_pressure_change,
        "STORM_SPEED": _read_number(
            current_input, ("STORM_SPEED", "stormSpeed", "storm_speed"),
            default=calculated_speed,
        ),
        "STORM_DIR": _read_number(
            current_input, ("STORM_DIR", "stormDirection", "storm_dir"),
            default=calculated_direction,
        ),
        "STARTING_MOVEMENT_SOURCE": movement_source,
    }

    # These fields are not used to predict the immediate next state, but are
    # retained for consistency when a caller inspects the returned start data.
    previous["STORM_SPEED"], previous["STORM_DIR"] = calculate_speed_direction(
        previous["LAT"], previous["LON"], current["LAT"], current["LON"], hours=3
    )
    return previous, current


def _prediction_point(state, forecast_hour, timestamp=None):
    """Format one model state for maps, tables, and uncertainty overlays."""
    return {
        "forecastHour": int(forecast_hour),
        "timestamp": timestamp.isoformat() if timestamp is not None else None,
        "lat": _rounded(state["LAT"]),
        "lon": _rounded(state["LON"]),
        "wind": _rounded(state["WIND"], 2),
        "pressure": _rounded(state["PRESSURE"], 2),
        "stormSpeed": _rounded(state["STORM_SPEED"], 2),
        "stormDirection": _rounded(state["STORM_DIR"], 2),
        "uncertaintyKm": _rounded(UNCERTAINTY_BY_HOUR_KM.get(int(forecast_hour), 60.0), 1),
        "isPrediction": forecast_hour > 0,
    }


def _impact_band(wind):
    """Return a transparent demonstration impact band from wind intensity."""
    if wind >= 64:
        return "Red", 115.0
    if wind >= 48:
        return "Orange", 85.0
    if wind >= 34:
        return "Yellow", 60.0
    return "Green", 35.0


def _build_impact_corridor(forecast_points):
    """Create map-circle data that widens with intensity and track uncertainty."""
    corridor = []
    for point in forecast_points:
        risk_level, wind_radius = _impact_band(point["wind"])
        corridor.append({
            "forecastHour": point["forecastHour"],
            "timestamp": point["timestamp"],
            "center": {"lat": point["lat"], "lon": point["lon"]},
            "riskLevel": risk_level,
            "windRadiusKm": wind_radius,
            "uncertaintyKm": point["uncertaintyKm"],
            "impactRadiusKm": _rounded(wind_radius + point["uncertaintyKm"], 1),
        })
    return corridor


def _archive_point(row, previous_row=None):
    """Turn one IBTrACS observation into a frontend-safe historical point."""
    speed = row["STORM_SPEED"]
    direction = row["STORM_DIR"]
    if previous_row is not None and (
        pd.isna(speed) or float(speed) < 0 or pd.isna(direction) or not 0 <= float(direction) <= 360
    ):
        hours = (row["ISO_TIME"] - previous_row["ISO_TIME"]).total_seconds() / 3600
        if hours > 0:
            speed, direction = calculate_speed_direction(
                previous_row["LAT"], previous_row["LON"], row["LAT"], row["LON"], hours
            )

    return {
        "timestamp": row["ISO_TIME"].isoformat(),
        "lat": _rounded(row["LAT"]),
        "lon": _rounded(row["LON"]),
        "wind": _rounded(row["WIND"], 2),
        "pressure": _rounded(row["PRESSURE"], 2),
        "stormSpeed": _rounded(speed, 2),
        "stormDirection": _rounded(direction, 2),
    }


def _historical_model_state(row):
    """Extract one archive row in the input format used by the simulator."""
    state = {
        "lat": _rounded(row["LAT"]),
        "lon": _rounded(row["LON"]),
        "wind": _rounded(row["WIND"], 2),
        "pressure": _rounded(row["PRESSURE"], 2),
        "latChange": _rounded(row["LAT_CHANGE"], 4),
        "lonChange": _rounded(row["LON_CHANGE"], 4),
        "windChange": _rounded(row["WIND_CHANGE"], 2),
        "pressureChange": _rounded(row["PRESSURE_CHANGE"], 2),
    }

    # Preserve historical storm speed/direction when valid. Otherwise the
    # simulator derives them from the previous and current coordinates.
    speed = _rounded(row["STORM_SPEED"], 2)
    direction = _rounded(row["STORM_DIR"], 2)
    if speed is not None and speed >= 0 and direction is not None and 0 <= direction <= 360:
        state["stormSpeed"] = speed
        state["stormDirection"] = direction
    return state


def _extract_forecast_points(payload):
    """Accept either a forecast array or the forecast object returned by this API."""
    raw_points = payload.get("forecast", payload.get("points"))
    if isinstance(raw_points, dict):
        raw_points = raw_points.get("points", raw_points.get("forecast"))
    if not isinstance(raw_points, list) or not raw_points:
        raise ValueError("Provide a non-empty 'forecast' list or object with a 'points' list.")

    points = []
    for index, point in enumerate(raw_points):
        if not isinstance(point, dict):
            raise ValueError(f"forecast item {index} must be an object.")
        points.append({
            "forecastHour": _read_number(
                point, ("forecastHour", "FORECAST_HOUR", "forecast_hour"), default=(index + 1) * 3
            ),
            "lat": _read_number(point, ("lat", "LAT", "latitude")),
            "lon": _read_number(point, ("lon", "LON", "longitude")),
            "wind": _read_number(point, ("wind", "WIND"), default=0.0),
            "pressure": _read_number(point, ("pressure", "PRESSURE"), default=None),
            "uncertaintyKm": _read_number(
                point, ("uncertaintyKm", "uncertainty_km"),
                default=UNCERTAINTY_BY_HOUR_KM.get((index + 1) * 3, 60.0),
            ),
            "timestamp": _read_text(point, ("timestamp", "ISO_TIME", "isoTime")),
        })
    return points


# ---- Active North Indian Ocean cyclone feed ---------------------------
# NOAA publishes this small IBTrACS subset for systems active in the previous
# seven days. It is separate from the local historical archive and is cached
# briefly so repeated frontend refreshes do not repeatedly download the file.

ACTIVE_IBTRACS_URL = (
    "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/"
    "v04r01/access/csv/ibtracs.ACTIVE.list.v04r01.csv"
)
ACTIVE_CYCLONE_CACHE_SECONDS = 15 * 60
active_cyclone_cache = {"expiresAt": 0.0, "cyclones": None}


def _valid_speed_direction(speed, direction):
    return (
        pd.notna(speed)
        and pd.notna(direction)
        and np.isfinite(float(speed))
        and np.isfinite(float(direction))
        and float(speed) >= 0
        and 0 <= float(direction) <= 360
    )


def _scaled_change(current_value, previous_value, hours):
    """Convert an observed movement interval to the model's 3-hour feature scale."""
    if hours <= 0:
        return 0.0
    return (float(current_value) - float(previous_value)) * 3.0 / hours


def _active_cyclone_simulation_input(track):
    """Prepare the latest active observation for the unchanged forecast API."""
    current_row = track.iloc[-1]
    current = {
        "lat": float(current_row["LAT"]),
        "lon": float(current_row["LON"]),
        "wind": float(current_row["WIND"]),
        "pressure": float(current_row["PRESSURE"]),
    }
    previous = None

    if len(track) >= 2:
        previous_row = track.iloc[-2]
        interval_hours = (current_row["ISO_TIME"] - previous_row["ISO_TIME"]).total_seconds() / 3600
        if interval_hours > 0:
            current.update({
                "latChange": _scaled_change(current_row["LAT"], previous_row["LAT"], interval_hours),
                "lonChange": _scaled_change(current_row["LON"], previous_row["LON"], interval_hours),
                "windChange": _scaled_change(current_row["WIND"], previous_row["WIND"], interval_hours),
                "pressureChange": _scaled_change(current_row["PRESSURE"], previous_row["PRESSURE"], interval_hours),
            })
            previous = {
                "lat": float(previous_row["LAT"]),
                "lon": float(previous_row["LON"]),
                "wind": float(previous_row["WIND"]),
                "pressure": float(previous_row["PRESSURE"]),
                "latChange": 0.0,
                "lonChange": 0.0,
                "windChange": 0.0,
                "pressureChange": 0.0,
            }
            if len(track) >= 3:
                earlier_row = track.iloc[-3]
                previous_interval_hours = (
                    previous_row["ISO_TIME"] - earlier_row["ISO_TIME"]
                ).total_seconds() / 3600
                if previous_interval_hours > 0:
                    previous.update({
                        "latChange": _scaled_change(previous_row["LAT"], earlier_row["LAT"], previous_interval_hours),
                        "lonChange": _scaled_change(previous_row["LON"], earlier_row["LON"], previous_interval_hours),
                        "windChange": _scaled_change(previous_row["WIND"], earlier_row["WIND"], previous_interval_hours),
                        "pressureChange": _scaled_change(previous_row["PRESSURE"], earlier_row["PRESSURE"], previous_interval_hours),
                    })

    if _valid_speed_direction(current_row["STORM_SPEED"], current_row["STORM_DIR"]):
        current["stormSpeed"] = float(current_row["STORM_SPEED"])
        current["stormDirection"] = float(current_row["STORM_DIR"])
    elif previous is not None:
        speed, direction = calculate_speed_direction(
            previous["lat"], previous["lon"], current["lat"], current["lon"], hours=3
        )
        current["stormSpeed"] = float(speed)
        current["stormDirection"] = float(direction)

    return {"current": current, **({"previous": previous} if previous is not None else {})}


def get_active_north_indian_cyclones():
    """Download and filter current NOAA IBTrACS records for BB and AS only."""
    if active_cyclone_cache["cyclones"] is not None and time.time() < active_cyclone_cache["expiresAt"]:
        return active_cyclone_cache["cyclones"]

    try:
        active_data = pd.read_csv(ACTIVE_IBTRACS_URL, skiprows=[1], low_memory=False)
    except (OSError, URLError, ValueError) as error:
        raise RuntimeError("The live IBTrACS active-cyclone feed is temporarily unavailable.") from error

    needed_columns = [
        "SID", "NAME", "SUBBASIN", "ISO_TIME", "LAT", "LON", "WMO_WIND", "WMO_PRES",
        "NEWDELHI_WIND", "NEWDELHI_PRES", "STORM_SPEED", "STORM_DIR",
    ]
    active_data = active_data[needed_columns].copy()
    active_data = active_data[active_data["SUBBASIN"].isin(["BB", "AS"])]
    for column in ["LAT", "LON", "WMO_WIND", "WMO_PRES", "NEWDELHI_WIND", "NEWDELHI_PRES", "STORM_SPEED", "STORM_DIR"]:
        active_data[column] = pd.to_numeric(active_data[column], errors="coerce")
    active_data["WIND"] = active_data["WMO_WIND"].fillna(active_data["NEWDELHI_WIND"])
    active_data["PRESSURE"] = active_data["WMO_PRES"].fillna(active_data["NEWDELHI_PRES"])
    active_data["ISO_TIME"] = pd.to_datetime(active_data["ISO_TIME"], errors="coerce")
    active_data = active_data.dropna(subset=["ISO_TIME", "LAT", "LON", "WIND", "PRESSURE"])

    cyclones = []
    for sid, storm in active_data.groupby("SID"):
        track = storm.sort_values("ISO_TIME").drop_duplicates(subset="ISO_TIME", keep="last").reset_index(drop=True)
        if track.empty:
            continue
        latest = track.iloc[-1]
        simulation_input = _active_cyclone_simulation_input(track)
        cyclone = {
            "sid": str(sid),
            "name": str(latest["NAME"]).strip() if pd.notna(latest["NAME"]) else "UNNAMED",
            "subbasin": str(latest["SUBBASIN"]),
            "observedAt": latest["ISO_TIME"].isoformat(),
            "lat": _rounded(latest["LAT"]),
            "lon": _rounded(latest["LON"]),
            "wind": _rounded(latest["WIND"], 1),
            "pressure": _rounded(latest["PRESSURE"], 1),
            "stormSpeed": _rounded(simulation_input["current"].get("stormSpeed"), 1),
            "stormDirection": _rounded(simulation_input["current"].get("stormDirection"), 1),
            "simulationInput": simulation_input,
        }
        cyclones.append(cyclone)

    cyclones.sort(key=lambda cyclone: cyclone["observedAt"], reverse=True)
    active_cyclone_cache["cyclones"] = cyclones
    active_cyclone_cache["expiresAt"] = time.time() + ACTIVE_CYCLONE_CACHE_SECONDS
    return cyclones


@app.route("/api/live-cyclones", methods=["GET"])
def list_active_cyclones():
    """List live NOAA observations that can be passed directly into the model."""
    try:
        cyclones = get_active_north_indian_cyclones()
        return jsonify({
            "dataType": "active-cyclone-observations",
            "source": "NOAA IBTrACS active dataset",
            "sourceNotice": "Active observations can be provisional and are refreshed from the source every 15 minutes.",
            "count": len(cyclones),
            "cyclones": cyclones,
        })
    except RuntimeError as error:
        return _api_error(str(error), 503)


# ---- Forecast endpoints ------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health_check():
    """Quick status endpoint for the frontend connection check."""
    return jsonify({
        "status": "ok",
        "model": "4 CatBoost recursive regressors with CHANGE_CHANGE features",
        "forecastHorizonHours": 12,
        "forecastStepHours": 3,
        "archiveCyclones": int(ni_data["SID"].nunique()),
    })


@app.route("/api/forecast", methods=["POST"])
def create_forecast():
    """Generate the requested 3, 6, 9 and 12-hour recursive simulation."""
    try:
        payload = _request_json_object()
        previous, current = _build_start_states(payload)

        # The requested prototype deliberately stops at 12 hours: recursion
        # compounds error beyond this point.
        raw_forecast = forecast_cyclone(previous, current, steps=4)
        start_timestamp = _read_text(payload, ("startTime", "start_time", "timestamp"))
        timestamp = pd.to_datetime(start_timestamp, errors="coerce") if start_timestamp else None
        if timestamp is not None and pd.isna(timestamp):
            raise ValueError("'startTime' must be a valid ISO date/time.")

        points = []
        for _, state in raw_forecast.iterrows():
            forecast_hour = int(state["FORECAST_HOUR"])
            point_time = timestamp + timedelta(hours=forecast_hour) if timestamp is not None else None
            points.append(_prediction_point(state, forecast_hour, point_time))

        origin = _prediction_point(current, 0, timestamp)
        origin["uncertaintyKm"] = 0.0
        # Lets the interface explain whether a user supplied movement directly,
        # supplied speed/direction, or started from a historical observation.
        origin["startingMovementSource"] = current["STARTING_MOVEMENT_SOURCE"]
        return jsonify({
            "dataType": "simulation",
            "notice": SIMULATION_NOTICE,
            "model": "CHANGE_CHANGE recursive CatBoost prototype",
            "forecastStepHours": 3,
            "forecastHorizonHours": 12,
            "origin": origin,
            "points": points,
            "trajectory": [origin, *points],
            "uncertaintyCorridor": [
                {
                    "forecastHour": point["forecastHour"],
                    "center": {"lat": point["lat"], "lon": point["lon"]},
                    "radiusKm": point["uncertaintyKm"],
                }
                for point in points
            ],
            "impactCorridor": _build_impact_corridor(points),
            "riskModelNotice": RISK_NOTICE,
        })
    except ValueError as error:
        return _api_error(str(error))


@app.route("/api/impact-corridor", methods=["POST"])
def create_impact_corridor():
    """Build dynamic Green/Yellow/Orange/Red map circles from a forecast path."""
    try:
        points = _extract_forecast_points(_request_json_object())
        return jsonify({
            "dataType": "prototype-impact-corridor",
            "notice": RISK_NOTICE,
            "method": "Impact radius = wind-intensity radius + forecast uncertainty radius.",
            "corridor": _build_impact_corridor(points),
        })
    except ValueError as error:
        return _api_error(str(error))


# ---- Historical archive endpoints -------------------------------------

@app.route("/api/archive/cyclones", methods=["GET"])
def list_historical_cyclones():
    """Search the North Indian Ocean archive by cyclone name and/or season."""
    name_query = request.args.get("name", request.args.get("query", "")).strip().upper()
    year_query = request.args.get("year", "").strip()
    try:
        limit = min(max(int(request.args.get("limit", 100)), 1), 500)
        if year_query:
            year = int(year_query)
        else:
            year = None
    except ValueError:
        return _api_error("'year' and 'limit' must be whole numbers.")

    filtered = ni_data
    if name_query:
        filtered = filtered[filtered["NAME"].fillna("").str.upper().str.contains(name_query, regex=False)]
    if year is not None:
        filtered = filtered[filtered["SEASON"] == year]

    summaries = (
        filtered.groupby("SID", as_index=False)
        .agg(
            name=("NAME", "first"),
            season=("SEASON", "first"),
            subbasin=("SUBBASIN", "first"),
            startTime=("ISO_TIME", "min"),
            endTime=("ISO_TIME", "max"),
            observations=("ISO_TIME", "size"),
        )
        .sort_values(["season", "startTime"], ascending=[False, False])
        .head(limit)
    )

    cyclones = []
    for _, item in summaries.iterrows():
        cyclones.append({
            "sid": str(item["SID"]),
            "name": str(item["name"]) if pd.notna(item["name"]) else "UNNAMED",
            "season": int(item["season"]),
            "subbasin": str(item["subbasin"]),
            "startTime": item["startTime"].isoformat(),
            "endTime": item["endTime"].isoformat(),
            "observations": int(item["observations"]),
        })

    return jsonify({
        "dataType": "historical-observations",
        "notice": HISTORICAL_NOTICE,
        "count": len(cyclones),
        "cyclones": cyclones,
    })


@app.route("/api/archive/cyclones/<sid>", methods=["GET"])
def get_historical_cyclone(sid):
    """Return every observation needed for map playback and its time slider."""
    cyclone = ni_data[ni_data["SID"].astype(str) == str(sid)].sort_values("ISO_TIME").reset_index(drop=True)
    if cyclone.empty:
        return _api_error(f"No cyclone with SID '{sid}' was found.", 404)

    points = []
    for index, row in cyclone.iterrows():
        previous_row = cyclone.iloc[index - 1] if index > 0 else None
        points.append(_archive_point(row, previous_row))

    first = cyclone.iloc[0]
    return jsonify({
        "dataType": "historical-observations",
        "notice": HISTORICAL_NOTICE,
        "cyclone": {
            "sid": str(first["SID"]),
            "name": str(first["NAME"]) if pd.notna(first["NAME"]) else "UNNAMED",
            "season": int(first["SEASON"]),
            "subbasin": str(first["SUBBASIN"]),
            "points": points,
        },
    })


@app.route("/api/archive/cyclones/<sid>/starting-state", methods=["GET"])
def get_historical_starting_state(sid):
    """Supply a real two-observation state for starting a model simulation."""
    try:
        point_index = int(request.args.get("pointIndex", 1))
    except ValueError:
        return _api_error("'pointIndex' must be a whole number.")

    cyclone = ni_data[ni_data["SID"].astype(str) == str(sid)].sort_values("ISO_TIME").reset_index(drop=True)
    if cyclone.empty:
        return _api_error(f"No cyclone with SID '{sid}' was found.", 404)
    if point_index < 1 or point_index >= len(cyclone):
        return _api_error(f"'pointIndex' must be between 1 and {len(cyclone) - 1}.")

    previous_row = cyclone.iloc[point_index - 1]
    current_row = cyclone.iloc[point_index]
    previous = {
        "lat": _rounded(previous_row["LAT"]),
        "lon": _rounded(previous_row["LON"]),
        "wind": _rounded(previous_row["WIND"], 2),
        "pressure": _rounded(previous_row["PRESSURE"], 2),
        "latChange": _rounded(previous_row["LAT_CHANGE"], 4),
        "lonChange": _rounded(previous_row["LON_CHANGE"], 4),
        "windChange": _rounded(previous_row["WIND_CHANGE"], 2),
        "pressureChange": _rounded(previous_row["PRESSURE_CHANGE"], 2),
    }
    current = {
        "lat": _rounded(current_row["LAT"]),
        "lon": _rounded(current_row["LON"]),
        "wind": _rounded(current_row["WIND"], 2),
        "pressure": _rounded(current_row["PRESSURE"], 2),
        "latChange": _rounded(current_row["LAT_CHANGE"], 4),
        "lonChange": _rounded(current_row["LON_CHANGE"], 4),
        "windChange": _rounded(current_row["WIND_CHANGE"], 2),
        "pressureChange": _rounded(current_row["PRESSURE_CHANGE"], 2),
        "stormSpeed": _rounded(current_row["STORM_SPEED"], 2),
        "stormDirection": _rounded(current_row["STORM_DIR"], 2),
    }
    return jsonify({
        "dataType": "historical-observations",
        "notice": HISTORICAL_NOTICE,
        "sid": str(sid),
        "pointIndex": point_index,
        "startTime": current_row["ISO_TIME"].isoformat(),
        "previous": previous,
        "current": current,
    })


@app.route("/api/archive/cyclones/<sid>/simulation-comparison", methods=["GET"])
def compare_historical_simulation(sid):
    """
    Compare a 12-hour recursive simulation with the next real observations.

    `pointIndex` identifies the current historical observation. It must have
    two earlier observations and four later 3-hour observations, so every
    model feature and each +3h to +12h verification point is valid.
    """
    try:
        point_index = int(request.args.get("pointIndex", 2))
    except ValueError:
        return _api_error("'pointIndex' must be a whole number.")

    cyclone = ni_data[ni_data["SID"].astype(str) == str(sid)].sort_values("ISO_TIME").reset_index(drop=True)
    if cyclone.empty:
        return _api_error(f"No cyclone with SID '{sid}' was found.", 404)
    maximum_start_index = len(cyclone) - 5
    if maximum_start_index < 2:
        return _api_error("This cyclone does not contain enough observations for a 12-hour comparison.")
    if point_index < 2 or point_index > maximum_start_index:
        return _api_error(
            f"'pointIndex' must be between 2 and {maximum_start_index} for a 12-hour comparison."
        )

    # The comparison is valid only for continuously sampled 3-hour IBTrACS
    # observations, matching the interval used when training the model.
    interval_rows = cyclone.iloc[point_index - 2: point_index + 5]
    gaps = interval_rows["ISO_TIME"].diff().dt.total_seconds().div(3600).dropna()
    if not (gaps == 3).all():
        return _api_error(
            "The selected point does not have a continuous 3-hour observation sequence. Choose another pointIndex."
        )

    previous_row = cyclone.iloc[point_index - 1]
    current_row = cyclone.iloc[point_index]
    previous_state, current_state = _build_start_states({
        "previous": _historical_model_state(previous_row),
        "current": _historical_model_state(current_row),
    })
    raw_forecast = forecast_cyclone(previous_state, current_state, steps=4)

    start_time = current_row["ISO_TIME"]
    origin = _archive_point(current_row, previous_row)
    origin["forecastHour"] = 0
    origin["isPrediction"] = False

    predicted_points = []
    actual_points = []
    comparison = []
    for step, (_, predicted_state) in enumerate(raw_forecast.iterrows(), start=1):
        forecast_hour = step * 3
        actual_row = cyclone.iloc[point_index + step]
        actual_previous_row = cyclone.iloc[point_index + step - 1]
        predicted_point = _prediction_point(
            predicted_state,
            forecast_hour,
            start_time + timedelta(hours=forecast_hour),
        )
        actual_point = _archive_point(actual_row, actual_previous_row)
        actual_point["forecastHour"] = forecast_hour
        actual_point["isPrediction"] = False

        track_error_km = float(haversine(
            actual_point["lat"], actual_point["lon"], predicted_point["lat"], predicted_point["lon"]
        ))
        wind_error_kt = abs(actual_point["wind"] - predicted_point["wind"])
        pressure_error_hpa = abs(actual_point["pressure"] - predicted_point["pressure"])

        predicted_points.append(predicted_point)
        actual_points.append(actual_point)
        comparison.append({
            "forecastHour": forecast_hour,
            "timestamp": actual_point["timestamp"],
            "actual": actual_point,
            "predicted": predicted_point,
            "trackErrorKm": _rounded(track_error_km, 2),
            "windErrorKt": _rounded(wind_error_kt, 2),
            "pressureErrorHpa": _rounded(pressure_error_hpa, 2),
        })

    first = cyclone.iloc[0]
    return jsonify({
        "dataType": "historical-simulation-comparison",
        "notice": (
            "Model-generated simulation compared against historical IBTrACS observations; "
            "not an official forecast or warning."
        ),
        "cyclone": {
            "sid": str(first["SID"]),
            "name": str(first["NAME"]) if pd.notna(first["NAME"]) else "UNNAMED",
            "season": int(first["SEASON"]),
            "subbasin": str(first["SUBBASIN"]),
        },
        "pointIndex": point_index,
        "startTime": start_time.isoformat(),
        "origin": origin,
        "predictedTrajectory": [origin, *predicted_points],
        "actualTrajectory": [origin, *actual_points],
        "comparison": comparison,
        "summary": {
            "meanTrackErrorKm": _rounded(np.mean([item["trackErrorKm"] for item in comparison]), 2),
            "meanWindErrorKt": _rounded(np.mean([item["windErrorKt"] for item in comparison]), 2),
            "meanPressureErrorHpa": _rounded(np.mean([item["pressureErrorHpa"] for item in comparison]), 2),
        },
    })


# ---- Settlement risk endpoint -----------------------------------------

def _risk_level(score):
    if score >= 75:
        return "Red", "Critical"
    if score >= 55:
        return "Orange", "High"
    if score >= 30:
        return "Yellow", "Moderate"
    return "Green", "Monitor"


@app.route("/api/risk/rank", methods=["POST"])
def rank_settlement_risk():
    """
    Rank caller-provided cities/villages against a forecast path.

    Score = up to 40 proximity points + 45 intensity points + 15 urgency
    points.  The individual components are returned to keep the demonstration
    transparent and explainable.
    """
    try:
        payload = _request_json_object()
        forecast_points = _extract_forecast_points(payload)
        settlements = payload.get("settlements")
        if not isinstance(settlements, list) or not settlements:
            raise ValueError("Provide a non-empty 'settlements' list with area/name, lat and lon.")

        rankings = []
        for index, settlement in enumerate(settlements):
            if not isinstance(settlement, dict):
                raise ValueError(f"settlement item {index} must be an object.")
            area = _read_text(settlement, ("area", "name", "village", "city"), default="Unnamed area")
            lat = _read_number(settlement, ("lat", "LAT", "latitude"))
            lon = _read_number(settlement, ("lon", "LON", "longitude"))

            distances = [
                float(haversine(lat, lon, point["lat"], point["lon"]))
                for point in forecast_points
            ]
            closest_index = int(np.argmin(distances))
            closest_point = forecast_points[closest_index]
            closest_distance = distances[closest_index]
            closest_hour = float(closest_point["forecastHour"])

            proximity_score = min(40.0, max(0.0, (1 - closest_distance / 300.0) * 40.0))
            intensity_score = min(45.0, max(0.0, closest_point["wind"] / 100.0 * 45.0))
            urgency_score = min(15.0, max(0.0, (1 - closest_hour / 12.0) * 15.0))
            score = proximity_score + intensity_score + urgency_score
            level, priority = _risk_level(score)

            rankings.append({
                "area": area,
                "lat": _rounded(lat),
                "lon": _rounded(lon),
                "riskLevel": level,
                "priority": priority,
                "riskScore": _rounded(score, 1),
                "estimatedClosestApproach": f"+{int(closest_hour)} h",
                "closestDistanceKm": _rounded(closest_distance, 1),
                "closestForecastHour": int(closest_hour),
                "predictedWindAtClosestApproach": _rounded(closest_point["wind"], 1),
                "scoreBreakdown": {
                    "distance": _rounded(proximity_score, 1),
                    "intensity": _rounded(intensity_score, 1),
                    "time": _rounded(urgency_score, 1),
                },
            })

        rankings.sort(key=lambda item: item["riskScore"], reverse=True)
        return jsonify({
            "dataType": "prototype-settlement-risk-ranking",
            "notice": RISK_NOTICE,
            "method": {
                "distance": "0–40 points; closer than the 300 km reference distance scores higher.",
                "intensity": "0–45 points; stronger predicted wind scores higher.",
                "time": "0–15 points; an earlier closest approach scores higher.",
            },
            "rankings": rankings,
        })
    except ValueError as error:
        return _api_error(str(error))


# Start the API only when this file is run directly.  It uses port 5000 by
# default; set an API_PORT environment variable if the frontend needs another.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("API_PORT", "5000")), debug=False)












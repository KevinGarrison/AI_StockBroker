######### Author: Pardis Ebrahimi ##########

from forecast_module import forecast_stock, prepare_forecast_data
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import FastAPI
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


logger = logging.getLogger(__name__)


app = FastAPI()


@app.get("/forecast/{ticker}")
async def get_forecast(ticker: str):
    try:
        df = await prepare_forecast_data(ticker)
        result = forecast_stock(ticker, df)
        logger.info(f'[FORECAST] forecast 5M: [{result}]')
        forecast_df = result.rename(columns={'RNN': 'y'})

        history_part = df[['ds', 'y']].copy()
        forecast_part = forecast_df[['ds', 'y']].copy()
        logger.info(f'[FORECAST] history: [{history_part}]')
        logger.info(f'[FORECAST] forecast 5M: [{forecast_part}]')


        final_result = {
            'history': history_part.to_dict(orient='records'),
            'forecast': forecast_part.to_dict(orient='records')
        }
        logger.info(f'[FORECAST] payload: [{final_result}]')

        encoded = jsonable_encoder(final_result)
        return JSONResponse(content=encoded, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

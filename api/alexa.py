"""Alexa Skill endpoint for FitnessAgent — Phase 1: Motivation."""

import os
import sys

# Allow imports from project root inside Vercel serverless
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from zoneinfo import ZoneInfo

from ask_sdk_core.dispatch_components import AbstractExceptionHandler, AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard
from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from lib.agent import generate_motivation_message
from lib.storage import get_recent_summary, save_record

app = FastAPI()

_SKILL_ID = os.getenv("ALEXA_SKILL_ID")
_TZ = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tokyo"))


def _trigger_time() -> str:
    hour = datetime.now(_TZ).hour
    return "朝" if hour < 12 else "夕方"


# ---------------------------------------------------------------------------
# Launch: Alexa スケジュールトリガーまたは手動起動
# ---------------------------------------------------------------------------

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        summary = get_recent_summary()
        time_of_day = _trigger_time()
        message = generate_motivation_message(
            trigger_time=time_of_day,
            record_summary=summary,
            phase=1,
        )
        speak = (
            f"{message} "
            "今日の運動、やりましたか？やったと言えばプラス1日カウントします。"
        )
        reprompt = "やった、またはまだと教えてください。"
        return (
            handler_input.response_builder
            .speak(speak)
            .ask(reprompt)
            .set_card(SimpleCard("FitnessAgent", message))
            .response
        )


# ---------------------------------------------------------------------------
# WorkoutDoneIntent: 「やった」と答えた場合
# ---------------------------------------------------------------------------

class WorkoutDoneIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("WorkoutDoneIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        save_record(did_workout=True)
        summary = get_recent_summary()
        speak = f"素晴らしい！記録しました。{summary} この調子でいきましょう！"
        return (
            handler_input.response_builder
            .speak(speak)
            .set_should_end_session(True)
            .response
        )


# ---------------------------------------------------------------------------
# WorkoutSkipIntent: 「まだ」「やってない」と答えた場合
# ---------------------------------------------------------------------------

class WorkoutSkipIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("WorkoutSkipIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        save_record(did_workout=False)
        time_of_day = _trigger_time()
        if time_of_day == "朝":
            speak = "わかりました。今日の夕方にまた声をかけます。諦めるな！"
        else:
            speak = "わかりました。記録しました。明日こそやりましょう！脂肪は待ってくれませんよ！"
        return (
            handler_input.response_builder
            .speak(speak)
            .set_should_end_session(True)
            .response
        )


# ---------------------------------------------------------------------------
# StatusIntent: 最近の記録を聞く
# ---------------------------------------------------------------------------

class StatusIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("StatusIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        summary = get_recent_summary()
        speak = f"あなたの記録です。{summary}"
        return (
            handler_input.response_builder
            .speak(speak)
            .set_should_end_session(True)
            .response
        )


# ---------------------------------------------------------------------------
# Built-in intents
# ---------------------------------------------------------------------------

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        speak = (
            "フィットネスエージェントです。"
            "「やった」で運動記録、「まだ」でスキップ、「記録を教えて」で履歴を確認できます。"
        )
        return (
            handler_input.response_builder
            .speak(speak)
            .ask(speak)
            .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name("AMAZON.CancelIntent")(handler_input) or is_intent_name(
            "AMAZON.StopIntent"
        )(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return (
            handler_input.response_builder
            .speak("またあとで！")
            .set_should_end_session(True)
            .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        print(f"[FitnessAgent] Error: {exception}")
        speak = "すみません、エラーが発生しました。もう一度試してください。"
        return handler_input.response_builder.speak(speak).response


# ---------------------------------------------------------------------------
# Skill builder
# ---------------------------------------------------------------------------

sb = SkillBuilder()
sb.skill_configuration.skill_id = _SKILL_ID

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(WorkoutDoneIntentHandler())
sb.add_request_handler(WorkoutSkipIntentHandler())
sb.add_request_handler(StatusIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

_webservice_handler = WebserviceSkillHandler(
    skill=sb.create(),
    verify_signature=True,
    verify_timestamp=True,
)


@app.post("/api/alexa")
async def alexa_endpoint(request: Request):
    body = (await request.body()).decode("utf-8")
    headers = dict(request.headers)
    response = _webservice_handler.verify_request_and_dispatch(
        http_request_headers=headers,
        http_request_body=body,
    )
    return JSONResponse(content=response)

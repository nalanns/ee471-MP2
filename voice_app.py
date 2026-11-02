import os
import re

import azure.cognitiveservices.speech as speechsdk
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("LIBRARY_API_URL", "http://127.0.0.1:5000/api")

COMMANDS = [
    ("create", r"^(create|add)\b"),
    ("list", r"^list\b"),
    ("get", r"^(get|show|find)\b"),
    ("replace", r"^replace\b"),
    ("update", r"^(update|change|edit)\b"),
    ("delete", r"^(delete|remove)\b"),
    ("checkout", r"^check[\s-]?out\b"),
    ("return", r"^return\b"),
    ("exit", r"^(exit|quit|stop|goodbye)\b"),
]

FIELD_PATTERN = re.compile(r"\b(type|title|author|page count|pages|duration)\b", re.IGNORECASE)


class ApiError(Exception):
    pass


def call_api(method, path, **kwargs):
    response = requests.request(method, f"{API_URL}{path}", timeout=5, **kwargs)
    print(f"[backend] {method} /api{path} -> {response.status_code}")
    data = response.json() if response.content else None
    if not response.ok:
        raise ApiError(data["error"] if data and "error" in data else f"request failed with status {response.status_code}.")
    return data


def detect_command(text):
    cleaned = text.strip().lower()
    for name, pattern in COMMANDS:
        if re.match(pattern, cleaned):
            return name
    return None


def parse_item_id(text):
    match = re.search(r"\bitem\s+(?:number\s+)?(\d+)", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def to_int(value):
    match = re.search(r"\d+", value.replace(",", ""))
    return int(match.group()) if match else value


def parse_fields(text):
    matches = list(FIELD_PATTERN.finditer(text))
    fields = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = text[match.end():end].strip(" ,.;:")
        key = match.group(1).lower()
        if key == "type":
            fields["type"] = "dvd" if "dvd" in value.lower() else value.lower()
        elif key in ("pages", "page count"):
            fields["page_count"] = to_int(value)
        elif key == "duration":
            fields["duration"] = to_int(value)
        else:
            fields[key] = value
    return fields


def kind(item):
    return "DVD" if item["type"] == "dvd" else "book"


def describe(item):
    extra = f"{item['page_count']} pages" if item["type"] == "book" else f"{item['duration']} minutes"
    status = "available" if item["is_available"] else "checked out"
    return f"Item {item['id']} is the {kind(item)} '{item['title']}' by {item['author']}, {extra}. It is {status}."


def list_filters(text):
    lowered = text.lower()
    params = {}
    if "available" in lowered:
        params["available"] = "true"
    elif "checked out" in lowered:
        params["available"] = "false"
    if "book" in lowered:
        params["type"] = "book"
    elif "dvd" in lowered:
        params["type"] = "dvd"
    return params


def handle(command, text):
    if command == "create":
        item = call_api("POST", "/items", json=parse_fields(text))
        return f"Successfully created {kind(item)} '{item['title']}' with ID {item['id']}."

    if command == "list":
        items = call_api("GET", "/items", params=list_filters(text))
        if not items:
            return "There are no matching items."
        names = "; ".join(f"item {item['id']}, '{item['title']}'" for item in items)
        noun = "item" if len(items) == 1 else "items"
        return f"I found {len(items)} {noun}: {names}."

    item_id = parse_item_id(text)
    if item_id is None:
        return "Sorry, I didn't catch the item number."

    if command == "get":
        return describe(call_api("GET", f"/items/{item_id}"))

    if command == "replace":
        item = call_api("PUT", f"/items/{item_id}", json=parse_fields(text))
        return f"Successfully replaced item {item_id}, '{item['title']}'."

    if command == "update":
        item = call_api("PATCH", f"/items/{item_id}", json=parse_fields(text))
        return f"Successfully updated item {item_id}, '{item['title']}'."

    if command == "delete":
        call_api("DELETE", f"/items/{item_id}")
        return f"Item {item_id} has been deleted."

    if command == "checkout":
        item = call_api("POST", f"/items/{item_id}/checkout")["item"]
        return f"Item {item_id}, '{item['title']}', has been checked out."

    if command == "return":
        item = call_api("POST", f"/items/{item_id}/return")["item"]
        return f"Item {item_id}, '{item['title']}', has been returned."


def respond(text):
    command = detect_command(text)
    if command is None:
        return "Sorry, I didn't understand that command."
    try:
        return handle(command, text)
    except ApiError as error:
        message = str(error)
        return f"Sorry, {message[0].lower()}{message[1:]}"
    except requests.ConnectionError:
        return "Sorry, I cannot reach the library server."


def main():
    speech_config = speechsdk.SpeechConfig(subscription=os.getenv("SPEECH_KEY"), region=os.getenv("SPEECH_REGION"))
    speech_config.speech_recognition_language = "en-US"
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=speechsdk.audio.AudioConfig(use_default_microphone=True),
    )
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=speechsdk.audio.AudioOutputConfig(use_default_speaker=True),
    )

    def speak(reply):
        print(f"Librarian: {reply}")
        synthesizer.speak_text_async(reply).get()

    speak("Hello, I am your librarian. How can I help you?")
    while True:
        print("\nListening...")
        result = recognizer.recognize_once_async().get()
        if result.reason == speechsdk.ResultReason.Canceled:
            details = result.cancellation_details
            print(f"Speech recognition canceled: {details.reason} {details.error_details}")
            break
        if result.reason != speechsdk.ResultReason.RecognizedSpeech:
            continue
        print(f"You: {result.text}")
        if detect_command(result.text) == "exit":
            speak("Goodbye.")
            break
        speak(respond(result.text))


if __name__ == "__main__":
    main()

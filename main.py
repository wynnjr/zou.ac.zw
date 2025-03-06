from chatbot import ChatBotService

if __name__ == "__main__":
    try:
        print("Chatbot is running. Press Ctrl+C to terminate.")
        ChatBotService().process_messages()
    except KeyboardInterrupt:
        print("Chatbot terminated.")

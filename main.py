from datetime import datetime
from bs4 import BeautifulSoup
import litellm # Added litellm
import config 
import gmail



def summarize_text_with_llm(text_to_summarize):
    print("\n--- Summarizing Text with LiteLLM  ---")
    if not text_to_summarize or len(text_to_summarize.strip()) < 50:  # Basic check
        print("Text too short or empty to summarize.")
        return "Text was too short or empty to provide a meaningful summary."

    max_chars = config.get_max_input_chars()  
    model = config.get_model()
    max_output_tokens = config.get_max_output_tokens()
    prompt_template = config.get_prompt_template()

    if len(text_to_summarize) > max_chars:
        print(f"Text is very long ({len(text_to_summarize)} chars), truncating to {max_chars} chars for summarization.")
        text_to_summarize = text_to_summarize[:max_chars]

    messages = [
        {
            "role": "user",
            "content": prompt_template.replace("{emails_raw}", text_to_summarize)
        }
    ]

    try:
        print(f"Using LiteLLM model: {model} for summarization.")

        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=0.7
        )
        
        # Accessing the response content according to LiteLLM's structure
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            summary = response.choices[0].message.content
            print("Summary generated successfully via LiteLLM.")
            return summary.strip()
        else:
            print("LiteLLM response format unexpected or content missing.")
            print("Full response object:", response)
            return "Could not generate summary due to unexpected API response format from LiteLLM."

    except litellm.exceptions.APIConnectionError as e:
        print(f"LiteLLM API Connection Error: {e}")
        return f"Error generating summary: API Connection Error - {e}"
    except litellm.exceptions.RateLimitError as e:
        print(f"LiteLLM Rate Limit Error: {e}")
        return f"Error generating summary: Rate Limit Exceeded - {e}"
    except litellm.exceptions.APIError as e: # Catch other API errors
        print(f"LiteLLM API Error: {e}")
        return f"Error generating summary: API Error - {e}"
    except Exception as e:
        print(f"An unexpected error occurred during summarization with LiteLLM: {e}")
        # You might want to log the full traceback here for debugging
        # import traceback
        # print(traceback.format_exc())
        return f"An unexpected error occurred with LiteLLM: {e}"


def summazrize_category(category):
    print(f"\n--- Processing Category: {category} ---")
    max_emails=config.get_gmail_max_results()  
    query = config.get_gmail_query()  

    emails_to_process = gmail.get_gmail_messages(query+category, max_emails)
    if not emails_to_process:
        print("No emails found to process.")
        return
    print(f"Retrieved email messages count {len(emails_to_process)}")

    all_extracted_text_for_summary = []

    for email_data in emails_to_process:
        print(f"\nProcessing Email ID: {email_data['id']}, Subject: {email_data['subject']} ...")
        
        # Optionally, summarize email body itself if no links
        email_body_to_summarize = email_data.get("body_text") or BeautifulSoup(email_data.get("body_html", ""),"html.parser").get_text()
        if email_body_to_summarize:
        #    all_extracted_text_for_summary.append(f"Content from email Received Fromn {email_data['from']} with Subject {email_data['subject']}:\n{email_body_to_summarize}\n\n")
           all_extracted_text_for_summary.append(f"""
            FROM: {email_data['from']}
            TO: {email_data['to']}
            SUBJECT: {email_data['subject']}
            DATE/TIME: {email_data['date_eastern']}
            BODY: {email_body_to_summarize}
            ------------------------------------------""")

    if not all_extracted_text_for_summary:
        print("\nNo content extracted from emails or links to summarize.")
        return

    print(f"\n--- Preparing to summarize all collected content ({len(all_extracted_text_for_summary)} sources) ---")
    combined_text = "".join(all_extracted_text_for_summary)
    
    final_summary = summarize_text_with_llm(combined_text)

    print(f"\n\n--- FINAL SUMMARY for {category} ---")
    print(final_summary)

# --- Main Execution Logic ---
def main():
    print(f"Starting GenAI Email Summarizer Agent...At {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    categories = config.get_gmail_categories()

    for category in categories:
        summazrize_category(category)

    print("\nGenAI Email Summarizer Agent finished.")

if __name__ == '__main__':
    main()




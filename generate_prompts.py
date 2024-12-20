"""
Midjourney Prompt Generator

This script generates creative prompts for Midjourney using OpenAI's Assistant API.

Setup:
1. Install requirements:
   pip install -r requirements.txt

2. Configure API credentials using either method:
   a) Create config.txt with:
      OPENAI_API_KEY=your_api_key
      ASSISTANT_ID=your_assistant_id
   
   b) Set environment variables:
      export OPENAI_API_KEY=your_api_key
      export ASSISTANT_ID=your_assistant_id

Usage:
  Generate default 500 prompts:
    python generate_prompts.py
  
  Generate custom number of prompts:
    python generate_prompts.py -n 5

The prompts will be saved to midjourney_prompts_YYMMDD.txt
"""

import os
import sys
import openai
import argparse
from datetime import datetime

def load_config():
    """Load configuration from config.txt file or environment variables."""
    config = {}
    required_keys = ['OPENAI_API_KEY', 'ASSISTANT_ID']
    
    # Try loading from config.txt first
    try:
        with open('config.txt', 'r') as file:
            for line in file:
                if '=' in line:
                    key, value = line.strip().split('=')
                    config[key] = value
    except FileNotFoundError:
        print("config.txt not found, checking environment variables...")
    
    # Check environment variables for any missing keys
    for key in required_keys:
        if key not in config:
            env_value = os.getenv(key)
            if env_value:
                config[key] = env_value
    
    # Verify all required keys are present
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(
            f"Missing required configuration keys: {', '.join(missing_keys)}\n"
            "Please either:\n"
            "1. Create a config.txt file with OPENAI_API_KEY and ASSISTANT_ID, or\n"
            "2. Set environment variables OPENAI_API_KEY and ASSISTANT_ID"
        )
    
    return config

def generate_topic_keywords(assistant_id):
    """Generate 5 combinations of topics and keywords."""
    thread = client.beta.threads.create()
    
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content='Generate 5 unique combinations of topics and keywords for creating Midjourney prompts. Each combination should have a main topic and 3-5 related keywords that can enhance the visual description. Format the response as a list with each line containing "Topic: [topic] | Keywords: [keyword1], [keyword2], [keyword3]". Make the combinations diverse and interesting.'
    )
    
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Wait for completion with timeout
    start_time = datetime.now()
    timeout_seconds = 30
    
    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run.status == 'completed':
            break
        
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > timeout_seconds:
            raise TimeoutError(f"OpenAI took too long to respond (>{timeout_seconds}s)")
    
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    combinations = messages.data[0].content[0].text.value.strip().split('\n')
    
    # Parse combinations into list of dictionaries
    result = []
    for combo in combinations:
        topic_part, keywords_part = combo.split(' | ')
        topic = topic_part.replace('Topic:', '').strip()
        keywords = [k.strip() for k in keywords_part.replace('Keywords:', '').split(',')]
        result.append({'topic': topic, 'keywords': keywords})
    
    return result

def generate_prompt(assistant_id, topic, keywords):
    """Generate a prompt based on specific topic and keywords."""
    thread = client.beta.threads.create()
    
    prompt_instruction = f"""Generate a detailed Midjourney prompt about the topic: {topic}
Using these keywords: {', '.join(keywords)}
Include artistic or photography style, lighting, mood, camera angle, and any relevant parameters.
Make it creative and unique. It could be portrait, wide or panoramic aspect ratio.
Do not include "/imagine prompt". For the prompt parameter, please make sure you use "--".
Do not add "." at the end of the prompt.
Your format response is just pure the prompt: [Your response here]"""
    
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt_instruction
    )
    
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Wait for completion with timeout
    start_time = datetime.now()
    timeout_seconds = 30
    
    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run.status == 'completed':
            break
        
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > timeout_seconds:
            raise TimeoutError(f"OpenAI took too long to respond (>{timeout_seconds}s)")
    
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value

def save_prompt(prompt):
    """Save a single prompt to today's file."""
    date_str = datetime.now().strftime('%y%m%d')
    filename = f'midjourney_prompts_{date_str}.txt'
    
    # Check if file exists and has content
    existing_content = ''
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            existing_content = file.read().strip()
    
    # Append prompt to file
    with open(filename, 'a') as file:
        # If file already has content, add newline before new prompt
        if existing_content:
            file.write('\n')
        file.write(prompt)
    
    return filename

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate Midjourney prompts using OpenAI Assistant')
    parser.add_argument('-n', '--num-prompts', type=int, default=500,
                      help='Number of prompts to generate (default: 500)')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    try:
        # Set up OpenAI client
        global client
        api_key = config['OPENAI_API_KEY']
        
        # Validate API key format
        if not api_key.startswith('sk-'):
            raise ValueError("Invalid API key format. Key should start with 'sk-'")
            
        client = openai.OpenAI(api_key=api_key)
        
        # Verify API key by making a simple API call
        try:
            client.models.list()
        except openai.AuthenticationError as e:
            raise ValueError(f"OpenAI API authentication failed. Please check your API key. Error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to verify API key: {str(e)}")
        
        # Get assistant ID from config
        assistant_id = config['ASSISTANT_ID']
        
        # Verify assistant ID
        try:
            client.beta.assistants.retrieve(assistant_id)
        except Exception as e:
            raise ValueError(f"Failed to retrieve assistant with ID {assistant_id}. Error: {str(e)}")
            
        print("Successfully authenticated with OpenAI API and verified assistant ID")
    except Exception as e:
        print(f"Setup error: {str(e)}")
        sys.exit(1)
    
    num_generated = 0
    total_chars = 0
    last_filename = None
    
    try:
        # Generate 5 topic-keyword combinations
        print("Generating topic-keyword combinations...")
        combinations = generate_topic_keywords(assistant_id)
        prompts_per_combo = args.num_prompts // len(combinations)
        
        # Generate prompts for each combination
        for combo in combinations:
            print(f"\nGenerating prompts for topic: {combo['topic']}")
            print(f"Using keywords: {', '.join(combo['keywords'])}")
            
            for i in range(prompts_per_combo):
                try:
                    prompt = generate_prompt(assistant_id, combo['topic'], combo['keywords']).strip()
                    last_filename = save_prompt(prompt)
                    num_generated += 1
                    total_chars += len(prompt)
                    
                    # Create a progress bar-like output
                    progress = (i + 1) / prompts_per_combo * 50
                    print(f"\rProgress: [{'=' * int(progress)}{' ' * (50 - int(progress))}] {i+1}/{prompts_per_combo}", end='')
                    print(f"\nGenerated and saved prompt {i+1}/{prompts_per_combo}:")
                    print(f"{prompt}\n")
                except Exception as e:
                    print(f"\nError generating prompt {i+1}: {str(e)}")
                    continue
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        if num_generated > 0:
            print(f"\nSuccessfully generated and saved {num_generated} prompts to {last_filename}")
        sys.exit(0)
    
    if num_generated > 0:
        print(f"\nSuccessfully generated and saved {num_generated} prompts ({total_chars} characters) to {last_filename}")

if __name__ == "__main__":
    main()

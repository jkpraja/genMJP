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
import signal
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

def generate_prompt(assistant_id):
    # Create a thread
    thread = client.beta.threads.create()
    
    # Add message to thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content='Generate a detailed Midjourney prompt about any topic. Include artistic or photography style, subject matter, lighting, mood, camera angle, and any relevant parameters. Make it creative or cozy and unique. It could be portrait, wide or even panaromic aspect ratio. Do not include "/imagine prompt". For the prompt parameter, please make sure you use "--". Do not add "." at the end of the prompt. Your format response is just pure the prompt: [Your response here]'
    )
    
    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Wait for completion
    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run.status == 'completed':
            break
    
    # Get the assistant's response
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value

def save_prompts(prompts):
    # Generate filename with date
    date_str = datetime.now().strftime('%y%m%d')
    filename = f'midjourney_prompts_{date_str}.txt'
    
    # Check if file exists and has content
    existing_content = ''
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            existing_content = file.read().strip()
    
    # Append prompts to file
    with open(filename, 'a') as file:
        # If file already has content, add newline before new prompts
        if existing_content:
            file.write('\n')
        file.write('\n'.join(prompts))
    
    return filename

def main():
    # Store prompts globally so signal handler can access them
    global generated_prompts
    generated_prompts = []
    
    def signal_handler(signum, frame):
        print("\nGracefully stopping... saving generated prompts...")
        if generated_prompts:
            filename = save_prompts(generated_prompts)
            print(f"\nSaved {len(generated_prompts)} prompts to {filename}")
        sys.exit(0)
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
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
    
    try:
        for i in range(args.num_prompts):
            try:
                prompt = generate_prompt(assistant_id).strip()  # Remove any extra whitespace
                generated_prompts.append(prompt)  # No newlines added
                # Create a progress bar-like output
                progress = (i + 1) / args.num_prompts * 50  # 50 characters wide
                print(f"\rProgress: [{'=' * int(progress)}{' ' * (50 - int(progress))}] {i+1}/{args.num_prompts}", end='')
                print(f"\nGenerated prompt {i+1}/{args.num_prompts}:")
                print(f"{prompt}\n")  # Display for monitoring
            except Exception as e:
                print(f"\nError generating prompt {i+1}: {str(e)}")
                continue
    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving generated prompts...")
        if generated_prompts:
            filename = save_prompts(generated_prompts)
            print(f"\nSaved {len(generated_prompts)} prompts to {filename}")
        sys.exit(0)
    
    # Save all prompts if completed successfully
    if generated_prompts:
        filename = save_prompts(generated_prompts)
        num_chars = sum(len(p) for p in generated_prompts)
        print(f"\nSuccessfully generated {len(generated_prompts)} prompts ({num_chars} characters) and saved to {filename}")

if __name__ == "__main__":
    main()

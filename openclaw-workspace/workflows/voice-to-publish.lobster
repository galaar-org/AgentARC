name: voice-to-publish
description: Convert voice note to multi-platform content and publish

args:
  audio_path: ""
  output_type: "all"  # blog, social, all
  platforms: ["wordpress", "twitter", "linkedin"]

steps:
  # Stage 1: Transcribe
  - id: transcribe
    command: |
      openclaw.invoke voice_to_content transcribe "$audio_path"
    description: "Transcribe audio to text"

  # Stage 2: Generate Blog (if needed)
  - id: generate_blog
    command: |
      openclaw.invoke voice_to_content blog "$audio_path"
    stdin: $transcribe.stdout
    condition: $output_type == "blog" || $output_type == "all"
    description: "Convert to blog post"

  # Stage 3: Generate Social (if needed)
  - id: generate_social
    command: |
      openclaw.invoke voice_to_content social "$audio_path"
    stdin: $transcribe.stdout
    condition: $output_type == "social" || $output_type == "all"
    description: "Convert to social content"

  # Stage 4: Extract Clips
  - id: clips
    command: |
      openclaw.invoke voice_to_content clips "$audio_path"
    stdin: $transcribe.stdout
    condition: $output_type == "all"
    description: "Extract quotable clips"

  # Stage 5: Fact Check
  - id: fact_check
    command: |
      openclaw.invoke fact_checker "$generate_blog.stdout"
    stdin: $generate_blog.stdout
    condition: $generate_blog.completed
    description: "Verify claims in blog"

  # Stage 6: Humanize Blog
  - id: humanize_blog
    command: |
      openclaw.invoke ai_trace_remover humanize "$fact_check.stdout"
    stdin: $fact_check.stdout
    condition: $fact_check.completed
    description: "Humanize blog content"

  # Stage 7: Humanize Social
  - id: humanize_social
    command: |
      openclaw.invoke ai_trace_remover light "$generate_social.stdout"
    stdin: $generate_social.stdout
    condition: $generate_social.completed
    description: "Humanize social content"

  # Stage 8: Review All
  - id: review
    command: |
      echo "Review all generated content"
    stdin: |
      Blog: $humanize_blog.stdout
      Social: $humanize_social.stdout
      Clips: $clips.stdout
    approval: required
    description: "Human approval"

  # Stage 9: Publish Blog
  - id: publish_blog
    command: |
      openclaw.invoke wordpress_publisher publish "$humanize_blog.stdout"
    condition: $review.approved && contains($platforms, "wordpress")
    description: "Publish to WordPress"

  # Stage 10: Publish Social
  - id: publish_social
    command: |
      openclaw.invoke social_poster all "$humanize_social.stdout"
    condition: $review.approved
    description: "Publish to social platforms"

  # Stage 11: Log
  - id: log
    command: |
      openclaw.invoke memory_log voice "$audio_path" "$platforms"
    description: "Log for tracking"

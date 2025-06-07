# Project Brief: PPTX Generator

## Overview
The `pptx-generator` is an open-source command-line interface (CLI) tool designed to automate the creation of PowerPoint presentations (.pptx files) from markdown content. It achieves this through a modular three-component architecture that combines AI-powered content analysis with template-driven presentation generation.

**Core Components:**
1. **Template Analyzer (`analyzer.py`)**
   - Inspects PPTX template files
   - Extracts available slide layouts and placeholders
   - Generates machine-readable layout definitions

2. **Content Processor (`processor.py`)**
   - Analyzes markdown content using LLM (via OpenRouter, model: deepseek/deepseek-chat-v3-0324:free)
   - Intelligently segments content into slides
   - Maps content to appropriate layouts

3. **Presentation Generator (`generator.py`)**
   - Creates final PPTX using template
   - Populates slides based on structured content
   - Maintains template styling and branding

## Key Features

1. **Intelligent Content Analysis**
   - LLM-powered content segmentation (via OpenRouter, model: deepseek/deepseek-chat-v3-0324:free)
   - Smart layout selection
   - Fallback to rule-based processing
   - Content type detection and mapping

2. **Template-Driven Generation**
   - Uses existing .pptx files as templates
   - Preserves master slides, themes, and fonts
   - Supports custom layouts and placeholders
   - Maintains brand consistency

3. **Modular Architecture**
   - Clear component separation
   - Well-defined data contracts
   - Robust error handling
   - Easy maintenance and extensions

4. **Structured Data Flow**
   - layouts.json for template capabilities
   - presentation.json for content structure
   - Validated data at each step
   - Clear error messaging

5. **Local Installation**
   - Simple setup process
   - Minimal dependencies
   - Clear documentation
   - Command-line interface

## Data Contracts

1. **layouts.json**
```json
{
  "layouts": [
    {
      "name": "Title Slide",
      "placeholders": [
        "Title 1",
        "Subtitle 2"
      ]
    }
  ]
}
```

2. **presentation.json**
```json
{
  "slides": [
    {
      "layout": "Title Slide",
      "content": {
        "Title 1": "Presentation Title",
        "Subtitle 2": "By Author Name"
      }
    }
  ]
}
```

## Error Handling

1. **Validation**
   - Template format verification
   - Layout compatibility checks
   - Content structure validation
   - File integrity verification

2. **Fallback Mechanisms**
   - Rule-based processing when LLM fails
   - Default layouts for unknown content types
   - Clear error reporting
   - Recovery strategies

## Future Vision
- Enhanced layout selection algorithms
- Support for more content types
- Advanced template analysis
- Batch processing capabilities
- Extended chart and image support

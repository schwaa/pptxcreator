# System Patterns

## Architecture Overview
```mermaid
flowchart TD
    Input[User Input: Markdown File] --> Analyzer[Template Analyzer]
    Template[Template PPTX] --> Analyzer
    Analyzer -->|layouts.json| Processor[Content Processor]
    Input --> Processor
    Processor -->|presentation.json| Generator[Presentation Generator]
    Template --> Generator
    Generator --> Output[Generated PPTX]

    subgraph Component 1: analyzer.py
        Analyzer
        AnalyzerValidation[Layout Validation]
        LayoutMapping[Layout Mapping]
    end

    subgraph Component 2: processor.py
        Processor
        LLMAnalysis[LLM Content Analysis via OpenRouter (deepseek/deepseek-chat-v3-0324:free)]
        Fallback[Rule-based Fallback]
        ContentValidation[Content Validation]
    end

    subgraph Component 3: generator.py
        Generator
        SlideCreation[Slide Creation]
        ContentPopulation[Content Population]
        OutputValidation[Output Validation]
    end
```

## Component Specifications

### 1. Template Analyzer (`analyzer.py`)
- **Purpose:** Extract and validate template layout information
- **Functions:**
  - Load and parse PPTX templates
  - Identify available layouts
  - Map placeholder locations
  - Generate layouts.json
- **Error Handling:**
  - Template format validation
  - Layout accessibility checks
  - Placeholder verification
  - Schema validation

### 2. Content Processor (`processor.py`)
- **Purpose:** Analyze content and map to layouts
- **Functions:**
  - Parse markdown input
  - Interface with LLM service (OpenRouter, model: deepseek/deepseek-chat-v3-0324:free)
  - Select appropriate layouts
  - Generate presentation.json
- **Error Handling:**
  - LLM service fallback (OpenRouter)
  - Content validation
  - Layout compatibility checks
  - Schema enforcement

### 3. Presentation Generator (`generator.py`)
- **Purpose:** Create final presentation
- **Functions:**
  - Load template and content
  - Create and populate slides
  - Apply styling and formatting
  - Save final PPTX
- **Error Handling:**
  - Input validation
  - Template consistency
  - Resource verification
  - Output validation

## Data Contracts

### 1. layouts.json
**Purpose:** Define available template layouts and capabilities
```json
{
  "layouts": [
    {
      "name": "Title Slide",
      "placeholders": [
        "Title 1",
        "Subtitle 2"
      ]
    },
    {
      "name": "Title and Content",
      "placeholders": [
        "Title 1",
        "Content Placeholder 2"
      ]
    },
    {
      "name": "Section Header",
      "placeholders": [
        "Title 1"
      ]
    }
  ]
}
```

### 2. presentation.json
**Purpose:** Define presentation content and structure
```json
{
  "slides": [
    {
      "layout": "Title Slide",
      "content": {
        "Title 1": "The Future of AI",
        "Subtitle 2": "A Presentation by Jane Doe"
      }
    },
    {
      "layout": "Title and Content",
      "content": {
        "Title 1": "Key Developments",
        "Content Placeholder 2": "- Rise of Transformers\n- Open Source Models\n- Multimodal Capabilities"
      }
    }
  ]
}
```

## Design Patterns

### 1. Strategy Pattern
- Applied in Content Processor for analysis methods:
  - LLM-based analysis (primary, via OpenRouter: deepseek/deepseek-chat-v3-0324:free)
  - Rule-based analysis (fallback)
  - Custom analysis plugins (future)

### 2. Factory Pattern
- Used for slide creation in Generator:
  - Different slide types
  - Layout-specific handling
  - Content type factories

### 3. Facade Pattern
- Simplifies complex operations behind CLI
- Hides component interaction details
- Provides unified error handling

### 4. Template Method Pattern
- Defines core generation workflow
- Allows customization of specific steps
- Maintains consistent process

## Error Handling Strategy

### 1. Validation Layers
- **Template Analysis:**
  - PPTX format verification
  - Layout accessibility
  - Placeholder presence
  
- **Content Processing:**
  - Markdown parsing
  - LLM response validation (from OpenRouter)
  - Layout compatibility
  
- **Generation:**
  - Resource availability
  - Content mapping
  - Output verification

### 2. Fallback Mechanisms
- LLM service (OpenRouter) unavailable → Rule-based processing
- Complex layout unavailable → Default layout
- Image missing → Placeholder or skip
- Chart data invalid → Text representation

## Performance Considerations

### 1. Resource Management
- Efficient template parsing
- Optimized file operations
- Memory-conscious processing
- Cleanup of temporary files

### 2. Progress Tracking
- Component-level progress
- Operation status updates
- Time remaining estimates
- Resource usage monitoring

### 3. Optimization Strategies
- Template caching
- Layout preprocessing
- Batch operations
- Parallel processing where possible

"""
Interactive Media Service

Handles creation and processing of interactive media content.
Provides comprehensive interactive content generation including HTML, SVG, 
interactive data visualizations, and accessibility-enhanced interactive elements.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import json
import base64
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session

from dryad.university.database.models_university import MediaAsset, MultimodalInteraction


class InteractiveMediaService:
    """
    Service for creating and processing interactive media content.
    
    Capabilities:
    - Interactive HTML content generation
    - SVG creation and animation
    - Data visualization generation
    - Interactive quiz and assessment creation
    - Accessibility features for interactive content
    - Web component generation
    """
    
    def __init__(self, db: Session):
        """Initialize the interactive media service"""
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Supported interactive formats
        self.supported_formats = ['.html', '.svg', '.json', '.xml', '.css', '.js']
        
        # Model configurations (would be loaded from actual models in production)
        self.templates = {
            'interactive_presentation': 'slide_template.html',
            'data_visualization': 'chart_template.svg',
            'quiz': 'quiz_template.html',
            'infographic': 'infographic_template.svg',
            'web_component': 'component_template.html'
        }
        
        # Interactive element types
        self.element_types = {
            'button': {'accessibility_role': 'button', 'required_attributes': ['aria-label']},
            'input': {'accessibility_role': 'textbox', 'required_attributes': ['aria-label', 'placeholder']},
            'select': {'accessibility_role': 'combobox', 'required_attributes': ['aria-label']},
            'checkbox': {'accessibility_role': 'checkbox', 'required_attributes': ['aria-label']},
            'radio': {'accessibility_role': 'radio', 'required_attributes': ['aria-label']},
            'link': {'accessibility_role': 'link', 'required_attributes': ['aria-label']},
            'img': {'accessibility_role': 'img', 'required_attributes': ['alt']},
            'table': {'accessibility_role': 'table', 'required_attributes': ['aria-label']},
            'form': {'accessibility_role': 'form', 'required_attributes': ['aria-label']}
        }
    
    async def generate_interactive_content(
        self,
        agent_id: str,
        content_type: str,
        content_spec: Dict[str, Any],
        accessibility_enhancement: bool = True
    ) -> Dict[str, Any]:
        """
        Generate interactive content based on specification.
        
        Args:
            agent_id: ID of the agent requesting generation
            content_type: Type of interactive content ('presentation', 'visualization', 'quiz', etc.)
            content_spec: Specification for the content (data, structure, styling, etc.)
            accessibility_enhancement: Whether to enhance with accessibility features
            
        Returns:
            Dict containing generated interactive content and metadata
        """
        try:
            start_time = datetime.now(timezone.utc)
            
            # Generate content based on type
            if content_type == 'presentation':
                result = await self._generate_interactive_presentation(content_spec)
            elif content_type == 'data_visualization':
                result = await self._generate_data_visualization(content_spec)
            elif content_type == 'quiz':
                result = await self._generate_interactive_quiz(content_spec)
            elif content_type == 'infographic':
                result = await self._generate_infographic(content_spec)
            elif content_type == 'web_component':
                result = await self._generate_web_component(content_spec)
            else:
                raise ValueError(f"Unsupported interactive content type: {content_type}")
            
            # Enhance with accessibility if requested
            if accessibility_enhancement:
                result = await self._enhance_interactive_accessibility(result, content_type)
            
            # Save generated content
            content_path = await self._save_interactive_content(result, content_type, content_spec)
            
            # Update result with path and metadata
            result['content_path'] = content_path
            result['content_type'] = content_type
            result['accessibility_enhanced'] = accessibility_enhancement
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            result['processing_time_seconds'] = processing_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating interactive content: {str(e)}")
            raise
    
    async def analyze_interactive_content(
        self,
        content_data: Union[str, bytes],
        content_type: str
    ) -> Dict[str, Any]:
        """
        Analyze interactive content for structure, accessibility, and functionality.
        
        Args:
            content_data: Interactive content file path or bytes
            content_type: Type of interactive content
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Load and parse content
            content = await self._load_interactive_content(content_data)
            
            # Perform analysis based on type
            analysis_results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'content_type': content_type,
                'content_length': len(content) if isinstance(content, str) else 0
            }
            
            # Structure analysis
            analysis_results['structure_analysis'] = await self._analyze_content_structure(content, content_type)
            
            # Accessibility analysis
            analysis_results['accessibility_analysis'] = await self._analyze_accessibility(content)
            
            # Interactive elements analysis
            analysis_results['interactive_elements'] = await self._analyze_interactive_elements(content)
            
            # Performance analysis
            analysis_results['performance_analysis'] = await self._analyze_performance(content)
            
            # Quality assessment
            analysis_results['quality_metrics'] = await self._assess_content_quality(analysis_results)
            
            # Generate recommendations
            analysis_results['recommendations'] = await self._generate_content_recommendations(analysis_results)
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Error analyzing interactive content: {str(e)}")
            raise
    
    async def create_accessible_interactive_elements(
        self,
        element_type: str,
        content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create or enhance interactive elements with accessibility features.
        
        Args:
            element_type: Type of interactive element
            content: Existing content or configuration
            context: Context information for accessibility enhancement
            
        Returns:
            Dict containing enhanced interactive elements
        """
        try:
            # Generate accessible element
            accessible_element = await self._generate_accessible_element(element_type, content, context)
            
            # Add accessibility attributes
            enhanced_element = await self._add_accessibility_attributes(accessible_element, context)
            
            # Test with screen readers (mock implementation)
            accessibility_test = await self._test_screen_reader_compatibility(enhanced_element)
            
            return {
                'element': enhanced_element,
                'accessibility_attributes': enhanced_element.get('attributes', {}),
                'accessibility_score': accessibility_test.get('score', 0.0),
                'screen_reader_compatible': accessibility_test.get('compatible', False),
                'recommendations': accessibility_test.get('recommendations', [])
            }
            
        except Exception as e:
            self.logger.error(f"Error creating accessible interactive elements: {str(e)}")
            raise
    
    async def _generate_interactive_presentation(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate interactive presentation content"""
        # Create HTML presentation with slides
        slides = spec.get('slides', [])
        theme = spec.get('theme', 'default')
        
        # Generate HTML structure
        html_content = self._create_presentation_html(slides, theme)
        
        # Generate CSS styling
        css_content = self._create_presentation_css(theme)
        
        # Generate JavaScript functionality
        js_content = self._create_presentation_js(slides)
        
        return {
            'html': html_content,
            'css': css_content,
            'javascript': js_content,
            'slides_count': len(slides),
            'theme': theme,
            'features': {
                'navigation': True,
                'keyboard_controls': True,
                'touch_support': True,
                'progress_indicator': True
            }
        }
    
    async def _generate_data_visualization(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate interactive data visualization"""
        chart_type = spec.get('chart_type', 'bar')
        data = spec.get('data', [])
        options = spec.get('options', {})
        
        if chart_type in ['line', 'bar', 'area']:
            # Generate SVG chart
            svg_content = self._create_svg_chart(chart_type, data, options)
            html_content = self._create_chart_html(svg_content, options)
        elif chart_type == 'pie':
            # Generate SVG pie chart
            svg_content = self._create_svg_pie_chart(data, options)
            html_content = self._create_chart_html(svg_content, options)
        else:
            # Default to bar chart
            svg_content = self._create_svg_chart('bar', data, options)
            html_content = self._create_chart_html(svg_content, options)
        
        # Generate interactive JavaScript
        js_content = self._create_chart_interactivity(data, chart_type)
        
        return {
            'html': html_content,
            'svg': svg_content,
            'javascript': js_content,
            'chart_type': chart_type,
            'data_points': len(data),
            'interactive_features': {
                'tooltips': True,
                'zoom': options.get('enable_zoom', False),
                'pan': options.get('enable_pan', False),
                'legend': True
            }
        }
    
    async def _generate_interactive_quiz(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate interactive quiz content"""
        questions = spec.get('questions', [])
        quiz_config = spec.get('config', {})
        
        # Generate HTML quiz structure
        html_content = self._create_quiz_html(questions, quiz_config)
        
        # Generate CSS for quiz styling
        css_content = self._create_quiz_css()
        
        # Generate JavaScript for quiz functionality
        js_content = self._create_quiz_js(questions, quiz_config)
        
        return {
            'html': html_content,
            'css': css_content,
            'javascript': js_content,
            'questions_count': len(questions),
            'quiz_features': {
                'immediate_feedback': quiz_config.get('immediate_feedback', True),
                'timer': quiz_config.get('enable_timer', False),
                'progress_tracking': True,
                'score_tracking': True,
                'retry_option': quiz_config.get('allow_retries', True)
            }
        }
    
    async def _generate_infographic(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate interactive infographic"""
        sections = spec.get('sections', [])
        style = spec.get('style', 'modern')
        
        # Generate SVG infographic
        svg_content = self._create_svg_infographic(sections, style)
        
        # Generate HTML wrapper
        html_content = self._create_infographic_html(svg_content, sections)
        
        # Generate JavaScript for interactivity
        js_content = self._create_infographic_interactivity(sections)
        
        return {
            'html': html_content,
            'svg': svg_content,
            'javascript': js_content,
            'sections_count': len(sections),
            'style': style,
            'features': {
                'scroll_animation': True,
                'hover_effects': True,
                'responsive_design': True,
                'accessibility': True
            }
        }
    
    async def _generate_web_component(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom web component"""
        component_name = spec.get('name', 'custom-component')
        template = spec.get('template', '')
        styles = spec.get('styles', '')
        script = spec.get('script', '')
        
        # Generate component HTML template
        html_template = self._create_component_template(component_name, template)
        
        # Generate component CSS
        css_content = self._create_component_css(component_name, styles)
        
        # Generate component JavaScript
        js_content = self._create_component_js(component_name, script)
        
        return {
            'html': html_template,
            'css': css_content,
            'javascript': js_content,
            'component_name': component_name,
            'features': {
                'shadow_dom': True,
                'properties': spec.get('properties', []),
                'events': spec.get('events', []),
                'slots': spec.get('slots', [])
            }
        }
    
    async def _enhance_interactive_accessibility(
        self,
        result: Dict[str, Any],
        content_type: str
    ) -> Dict[str, Any]:
        """Enhance interactive content with accessibility features"""
        # Add ARIA labels and roles
        enhanced_content = result.copy()
        
        if 'html' in enhanced_content:
            enhanced_content['html'] = await self._add_aria_attributes(
                enhanced_content['html'], content_type
            )
        
        if 'svg' in enhanced_content:
            enhanced_content['svg'] = await self._add_svg_accessibility(
                enhanced_content['svg'], content_type
            )
        
        # Add keyboard navigation
        if 'javascript' in enhanced_content:
            enhanced_content['javascript'] = await self._add_keyboard_navigation(
                enhanced_content['javascript'], content_type
            )
        
        # Add screen reader support
        enhanced_content['accessibility_features'] = {
            'aria_labels': True,
            'keyboard_navigation': True,
            'screen_reader_support': True,
            'focus_management': True,
            'high_contrast_support': True
        }
        
        return enhanced_content
    
    async def _load_interactive_content(self, content_data: Union[str, bytes]) -> str:
        """Load interactive content from file or bytes"""
        try:
            if isinstance(content_data, str):
                # Load from file path
                with open(content_data, 'r', encoding='utf-8') as f:
                    return f.read()
            elif isinstance(content_data, bytes):
                # Load from bytes
                return content_data.decode('utf-8')
            else:
                raise ValueError("Invalid content data type")
                
        except Exception as e:
            self.logger.error(f"Error loading interactive content: {str(e)}")
            raise
    
    async def _save_interactive_content(
        self,
        content: Dict[str, Any],
        content_type: str,
        spec: Dict[str, Any]
    ) -> str:
        """Save generated interactive content to files"""
        try:
            from pathlib import Path
            
            # Create output directory
            output_dir = Path("generated_interactive")
            output_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"interactive_{content_type}_{timestamp}"
            
            saved_files = {}
            
            # Save HTML
            if 'html' in content:
                html_path = output_dir / f"{base_filename}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(content['html'])
                saved_files['html'] = str(html_path)
            
            # Save CSS
            if 'css' in content:
                css_path = output_dir / f"{base_filename}.css"
                with open(css_path, 'w', encoding='utf-8') as f:
                    f.write(content['css'])
                saved_files['css'] = str(css_path)
            
            # Save JavaScript
            if 'javascript' in content:
                js_path = output_dir / f"{base_filename}.js"
                with open(js_path, 'w', encoding='utf-8') as f:
                    f.write(content['javascript'])
                saved_files['javascript'] = str(js_path)
            
            # Save SVG
            if 'svg' in content:
                svg_path = output_dir / f"{base_filename}.svg"
                with open(svg_path, 'w', encoding='utf-8') as f:
                    f.write(content['svg'])
                saved_files['svg'] = str(svg_path)
            
            # Return primary file path (HTML if available, otherwise first file)
            if 'html' in saved_files:
                return saved_files['html']
            elif saved_files:
                return list(saved_files.values())[0]
            else:
                return str(output_dir / f"{base_filename}.txt")
            
        except Exception as e:
            self.logger.error(f"Error saving interactive content: {str(e)}")
            raise
    
    def _create_presentation_html(self, slides: List[Dict[str, Any]], theme: str) -> str:
        """Create HTML structure for interactive presentation"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"    <title>Interactive Presentation - {theme}</title>",
            "    <link rel='stylesheet' href='presentation.css'>",
            "</head>",
            "<body>",
            "    <div class='presentation-container'>",
            "        <div class='slide-container'>"
        ]
        
        for i, slide in enumerate(slides):
            html_parts.extend([
                f"            <div class='slide' id='slide-{i+1}'>",
                f"                <div class='slide-content'>",
                f"                    <h2>{slide.get('title', f'Slide {i+1}')}</h2>",
                f"                    <div class='slide-body'>{slide.get('content', '')}</div>",
                "                </div>",
                "            </div>"
            ])
        
        html_parts.extend([
            "        </div>",
            "        <div class='controls'>",
            "            <button id='prev-btn' aria-label='Previous slide'>Previous</button>",
            "            <span id='slide-counter' aria-live='polite'></span>",
            "            <button id='next-btn' aria-label='Next slide'>Next</button>",
            "        </div>",
            "    </div>",
            "    <script src='presentation.js'></script>",
            "</body>",
            "</html>"
        ])
        
        return '\n'.join(html_parts)
    
    def _create_presentation_css(self, theme: str) -> str:
        """Create CSS for interactive presentation"""
        return """
/* Interactive Presentation Styles */
.presentation-container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    position: relative;
}

.slide-container {
    position: relative;
    overflow: hidden;
    height: 600px;
    border: 2px solid #333;
    border-radius: 8px;
}

.slide {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    padding: 40px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.5s ease-in-out;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.slide.active {
    opacity: 1;
    transform: translateX(0);
}

.slide.prev {
    transform: translateX(-100%);
}

.slide-content {
    max-width: 800px;
    margin: 0 auto;
    text-align: center;
}

.slide h2 {
    font-size: 2.5rem;
    margin-bottom: 2rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.slide-body {
    font-size: 1.2rem;
    line-height: 1.6;
}

.controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    padding: 0 20px;
}

.controls button {
    padding: 12px 24px;
    font-size: 16px;
    border: none;
    border-radius: 6px;
    background: #667eea;
    color: white;
    cursor: pointer;
    transition: background 0.3s ease;
}

.controls button:hover {
    background: #5a6fd8;
}

.controls button:focus {
    outline: 2px solid #ff6b6b;
    outline-offset: 2px;
}

#slide-counter {
    font-size: 18px;
    font-weight: bold;
    color: #333;
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
    .slide {
        transition: none;
    }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    .slide {
        background: #000;
        color: #fff;
        border: 2px solid #fff;
    }
}
        """.strip()
    
    def _create_presentation_js(self, slides: List[Dict[str, Any]]) -> str:
        """Create JavaScript for interactive presentation functionality"""
        return f"""
// Interactive Presentation JavaScript
class PresentationController {{
    constructor() {{
        this.currentSlide = 0;
        this.totalSlides = {len(slides)};
        this.slides = document.querySelectorAll('.slide');
        this.prevBtn = document.getElementById('prev-btn');
        this.nextBtn = document.getElementById('next-btn');
        this.counter = document.getElementById('slide-counter');
        
        this.init();
    }}
    
    init() {{
        this.updateDisplay();
        this.bindEvents();
        this.showSlide(0);
    }}
    
    bindEvents() {{
        this.prevBtn.addEventListener('click', () => this.previousSlide());
        this.nextBtn.addEventListener('click', () => this.nextSlide());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            switch(e.key) {{
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    this.previousSlide();
                    break;
                case 'ArrowRight':
                case 'ArrowDown':
                case ' ':
                    e.preventDefault();
                    this.nextSlide();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.showSlide(0);
                    break;
                case 'End':
                    e.preventDefault();
                    this.showSlide(this.totalSlides - 1);
                    break;
            }}
        }});
    }}
    
    showSlide(index) {{
        if (index < 0 || index >= this.totalSlides) return;
        
        this.slides.forEach((slide, i) => {{
            slide.classList.remove('active', 'prev');
            if (i === index) {{
                slide.classList.add('active');
            }} else if (i < index) {{
                slide.classList.add('prev');
            }}
        }});
        
        this.currentSlide = index;
        this.updateDisplay();
        this.announceSlide();
    }}
    
    nextSlide() {{
        if (this.currentSlide < this.totalSlides - 1) {{
            this.showSlide(this.currentSlide + 1);
        }}
    }}
    
    previousSlide() {{
        if (this.currentSlide > 0) {{
            this.showSlide(this.currentSlide - 1);
        }}
    }}
    
    updateDisplay() {{
        this.counter.textContent = `${{this.currentSlide + 1}} / ${{this.totalSlides}}`;
        
        this.prevBtn.disabled = this.currentSlide === 0;
        this.nextBtn.disabled = this.currentSlide === this.totalSlides - 1;
    }}
    
    announceSlide() {{
        const announcement = `Slide ${{this.currentSlide + 1}} of ${{this.totalSlides}}`;
        this.counter.setAttribute('aria-label', announcement);
    }}
}}

// Initialize presentation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {{
    new PresentationController();
}});
        """.strip()
    
    def _create_svg_chart(
        self,
        chart_type: str,
        data: List[Dict[str, Any]],
        options: Dict[str, Any]
    ) -> str:
        """Create SVG chart visualization"""
        # Simple bar chart implementation
        width = options.get('width', 800)
        height = options.get('height', 400)
        margin = 60
        
        # Calculate dimensions
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        # Mock data processing
        values = [item.get('value', 0) for item in data]
        max_value = max(values) if values else 100
        
        svg_parts = [
            f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg' role='img' aria-labelledby='chart-title chart-desc'>",
            f"<title id='chart-title'>{options.get('title', 'Data Chart')}</title>",
            f"<desc id='chart-desc'>{options.get('description', 'Data visualization chart')}</desc>"
        ]
        
        # Add background
        svg_parts.append(f"<rect x='0' y='0' width='{width}' height='{height}' fill='{options.get('background_color', '#f8f9fa')}'/>")
        
        # Draw bars
        bar_width = chart_width / len(data) * 0.8
        gap = chart_width / len(data) * 0.2
        
        for i, item in enumerate(data):
            value = item.get('value', 0)
            bar_height = (value / max_value) * chart_height
            x = margin + i * (bar_width + gap)
            y = height - margin - bar_height
            
            color = item.get('color', '#667eea')
            label = item.get('label', f'Item {i+1}')
            
            # Add bar with accessibility
            svg_parts.append(
                f"<rect x='{x:.1f}' y='{y:.1f}' width='{bar_width:.1f}' height='{bar_height:.1f}' "
                f"fill='{color}' stroke='#333' stroke-width='1' "
                f"role='graphics-symbol' aria-label='{label}: {value}'/>"
            )
            
            # Add label
            svg_parts.append(
                f"<text x='{x + bar_width/2:.1f}' y='{height - margin + 20}' "
                f"text-anchor='middle' font-size='12' fill='#333'>{label}</text>"
            )
        
        # Add axes
        svg_parts.append(f"<line x1='{margin}' y1='{height - margin}' x2='{width - margin}' y2='{height - margin}' stroke='#333' stroke-width='2'/>")
        svg_parts.append(f"<line x1='{margin}' y1='{margin}' x2='{margin}' y2='{height - margin}' stroke='#333' stroke-width='2'/>")
        
        svg_parts.append("</svg>")
        
        return '\n'.join(svg_parts)
    
    def _create_svg_pie_chart(
        self,
        data: List[Dict[str, Any]],
        options: Dict[str, Any]
    ) -> str:
        """Create SVG pie chart"""
        width = options.get('width', 400)
        height = options.get('height', 400)
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 3
        
        # Calculate total and angles
        total = sum(item.get('value', 0) for item in data)
        if total == 0:
            total = 1  # Avoid division by zero
        
        svg_parts = [
            f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg' role='img' aria-labelledby='pie-title pie-desc'>",
            f"<title id='pie-title'>{options.get('title', 'Pie Chart')}</title>",
            f"<desc id='pie-desc'>{options.get('description', 'Pie chart showing data distribution')}</desc>"
        ]
        
        # Draw pie slices
        current_angle = 0
        for i, item in enumerate(data):
            value = item.get('value', 0)
            slice_angle = (value / total) * 360
            
            # Calculate slice path
            start_angle = current_angle
            end_angle = current_angle + slice_angle
            
            start_x = center_x + radius * np.cos(np.radians(start_angle))
            start_y = center_y + radius * np.sin(np.radians(start_angle))
            end_x = center_x + radius * np.cos(np.radians(end_angle))
            end_y = center_y + radius * np.sin(np.radians(end_angle))
            
            large_arc = slice_angle > 180
            
            path_data = f"M {center_x} {center_y} L {start_x} {start_y} A {radius} {radius} 0 {int(large_arc)} 1 {end_x} {end_y} Z"
            
            color = item.get('color', f'hsl({i * 60}, 70%, 60%)')
            label = item.get('label', f'Item {i+1}')
            
            # Add slice with accessibility
            svg_parts.append(
                f"<path d='{path_data}' fill='{color}' stroke='#fff' stroke-width='2' "
                f"role='graphics-symbol' aria-label='{label}: {value} ({value/total*100:.1f}%)'/>"
            )
            
            current_angle += slice_angle
        
        svg_parts.append("</svg>")
        
        return '\n'.join(svg_parts)
    
    def _create_chart_html(self, svg_content: str, options: Dict[str, Any]) -> str:
        """Create HTML wrapper for chart"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{options.get('title', 'Data Visualization')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f8f9fa;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .chart-title {{
            font-size: 1.5rem;
            margin-bottom: 10px;
            color: #333;
        }}
        svg {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
    <div class="chart-container">
        <h1 class="chart-title">{options.get('title', 'Data Visualization')}</h1>
        {svg_content}
    </div>
</body>
</html>
        """.strip()
    
    def _create_chart_interactivity(self, data: List[Dict[str, Any]], chart_type: str) -> str:
        """Create JavaScript for chart interactivity"""
        return f"""
// Chart Interactivity
document.addEventListener('DOMContentLoaded', function() {{
    const chartElements = document.querySelectorAll('[role="graphics-symbol"]');
    
    chartElements.forEach(element => {{
        element.addEventListener('mouseenter', function() {{
            this.style.opacity = '0.8';
            this.style.transform = 'scale(1.05)';
            this.style.transition = 'all 0.3s ease';
        }});
        
        element.addEventListener('mouseleave', function() {{
            this.style.opacity = '1';
            this.style.transform = 'scale(1)';
        }});
        
        // Keyboard accessibility
        element.setAttribute('tabindex', '0');
        element.addEventListener('focus', function() {{
            this.style.outline = '2px solid #667eea';
            this.style.outlineOffset = '2px';
        }});
        
        element.addEventListener('blur', function() {{
            this.style.outline = 'none';
        }});
    }});
}});
        """.strip()
    
    def _create_quiz_html(self, questions: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Create HTML for interactive quiz"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "    <meta charset='UTF-8'>",
            "    <meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            "    <title>Interactive Quiz</title>",
            "    <link rel='stylesheet' href='quiz.css'>",
            "</head>",
            "<body>",
            "    <div class='quiz-container'>",
            "        <header class='quiz-header'>",
            "            <h1>Interactive Quiz</h1>",
            "            <div class='progress-bar'>",
            "                <div id='progress-fill'></div>",
            "            </div>",
            "        </header>",
            "        <main class='quiz-content'>"
        ]
        
        for i, question in enumerate(questions):
            question_id = f"q{i+1}"
            html_parts.extend([
                f"            <div class='question' id='{question_id}' data-question='{i+1}'>",
                f"                <h2>Question {i+1}</h2>",
                f"                <p class='question-text'>{question.get('text', '')}</p>",
                "                <div class='options'>"
            ])
            
            options = question.get('options', [])
            for j, option in enumerate(options):
                option_id = f"{question_id}_option_{j+1}"
                html_parts.extend([
                    "                    <div class='option'>",
                    f"                        <input type='{question.get('type', 'radio')}' id='{option_id}' name='{question_id}' value='{j+1}'>",
                    f"                        <label for='{option_id}'>{option}</label>",
                    "                    </div>"
                ])
            
            html_parts.extend([
                "                </div>",
                "                <div class='feedback' id='feedback_{i+1}'></div>",
                "            </div>"
            ])
        
        html_parts.extend([
            "        </main>",
            "        <footer class='quiz-footer'>",
            "            <button id='submit-btn'>Submit Quiz</button>",
            "            <button id='retry-btn'>Retry</button>",
            "            <div id='score-display'></div>",
            "        </footer>",
            "    </div>",
            "    <script src='quiz.js'></script>",
            "</body>",
            "</html>"
        ])
        
        return '\n'.join(html_parts)
    
    def _create_quiz_css(self) -> str:
        """Create CSS for quiz styling"""
        return """
/* Quiz Styles */
.quiz-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.quiz-header {
    text-align: center;
    margin-bottom: 30px;
}

.quiz-header h1 {
    color: #333;
    margin-bottom: 20px;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
    overflow: hidden;
}

#progress-fill {
    height: 100%;
    background: #667eea;
    width: 0%;
    transition: width 0.3s ease;
}

.question {
    margin-bottom: 30px;
    padding: 20px;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    display: none;
}

.question.active {
    display: block;
}

.question h2 {
    color: #667eea;
    margin-bottom: 15px;
}

.question-text {
    font-size: 1.1rem;
    margin-bottom: 20px;
    line-height: 1.6;
}

.options {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.option {
    display: flex;
    align-items: center;
    padding: 10px;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s ease;
}

.option:hover {
    background: #f8f9fa;
}

.option input[type="radio"],
.option input[type="checkbox"] {
    margin-right: 10px;
}

.option label {
    cursor: pointer;
    flex: 1;
}

.feedback {
    margin-top: 15px;
    padding: 10px;
    border-radius: 4px;
    display: none;
}

.feedback.correct {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.feedback.incorrect {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.quiz-footer {
    text-align: center;
    margin-top: 30px;
}

.quiz-footer button {
    padding: 12px 24px;
    margin: 0 10px;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    cursor: pointer;
    transition: background 0.3s ease;
}

#submit-btn {
    background: #28a745;
    color: white;
}

#submit-btn:hover {
    background: #218838;
}

#retry-btn {
    background: #6c757d;
    color: white;
    display: none;
}

#retry-btn:hover {
    background: #5a6268;
}

#retry-btn.show {
    display: inline-block;
}

#score-display {
    margin-top: 20px;
    font-size: 1.2rem;
    font-weight: bold;
    color: #667eea;
}

/* Accessibility */
.option:focus-within {
    outline: 2px solid #667eea;
    outline-offset: 2px;
}

button:focus {
    outline: 2px solid #667eea;
    outline-offset: 2px;
}

/* High contrast mode */
@media (prefers-contrast: high) {
    .question {
        border: 2px solid #000;
    }
    
    .option {
        border: 2px solid #000;
    }
}
        """.strip()
    
    def _create_quiz_js(self, questions: List[Dict[str, Any]], config: Dict[str, Any]) -> str:
        """Create JavaScript for quiz functionality"""
        return f"""
// Quiz JavaScript
class InteractiveQuiz {{
    constructor() {{
        this.questions = {json.dumps(questions)};
        this.currentQuestion = 0;
        this.score = 0;
        this.userAnswers = new Array(this.questions.length).fill(null);
        this.init();
    }}
    
    init() {{
        this.bindEvents();
        this.showQuestion(0);
        this.updateProgress();
    }}
    
    bindEvents() {{
        const submitBtn = document.getElementById('submit-btn');
        const retryBtn = document.getElementById('retry-btn');
        
        submitBtn.addEventListener('click', () => this.submitQuiz());
        retryBtn.addEventListener('click', () => this.retryQuiz());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Enter' && e.target.type === 'radio') {{
                this.selectAnswer();
            }}
        }});
    }}
    
    showQuestion(index) {{
        // Hide all questions
        document.querySelectorAll('.question').forEach(q => q.classList.remove('active'));
        
        // Show current question
        const currentQ = document.querySelector(`[data-question="${{index + 1}}"]`);
        if (currentQ) {{
            currentQ.classList.add('active');
        }}
        
        // Focus on first option
        const firstOption = currentQ?.querySelector('input[type="radio"], input[type="checkbox"]');
        if (firstOption) {{
            firstOption.focus();
        }}
    }}
    
    selectAnswer() {{
        const activeQuestion = document.querySelector('.question.active');
        if (!activeQuestion) return;
        
        const selectedOption = activeQuestion.querySelector('input[type="radio"]:checked, input[type="checkbox"]:checked');
        if (selectedOption) {{
            const questionIndex = parseInt(activeQuestion.dataset.question) - 1;
            this.userAnswers[questionIndex] = parseInt(selectedOption.value);
            
            // Provide immediate feedback if enabled
            {'''
            if (''' + str(config.get('immediate_feedback', True)).lower() + ''') {
                this.showImmediateFeedback(questionIndex, selectedOption);
            }
            '''}
        }}
    }}
    
    showImmediateFeedback(questionIndex, selectedOption) {{
        const question = this.questions[questionIndex];
        const feedbackDiv = document.getElementById(`feedback_${{questionIndex + 1}}`);
        const isCorrect = parseInt(selectedOption.value) === question.correct_answer;
        
        feedbackDiv.className = 'feedback ' + (isCorrect ? 'correct' : 'incorrect');
        feedbackDiv.textContent = isCorrect ? 'Correct!' : 'Incorrect. Please try again.';
        feedbackDiv.style.display = 'block';
        
        // Announce to screen readers
        feedbackDiv.setAttribute('aria-live', 'polite');
    }}
    
    updateProgress() {{
        const progress = ((this.currentQuestion + 1) / this.questions.length) * 100;
        document.getElementById('progress-fill').style.width = progress + '%';
    }}
    
    nextQuestion() {{
        if (this.currentQuestion < this.questions.length - 1) {{
            this.currentQuestion++;
            this.showQuestion(this.currentQuestion);
            this.updateProgress();
        }}
    }}
    
    submitQuiz() {{
        // Calculate score
        this.score = 0;
        for (let i = 0; i < this.questions.length; i++) {{
            const correctAnswer = this.questions[i].correct_answer;
            if (this.userAnswers[i] === correctAnswer) {{
                this.score++;
            }}
        }}
        
        const percentage = (this.score / this.questions.length) * 100;
        
        // Display results
        const scoreDisplay = document.getElementById('score-display');
        scoreDisplay.textContent = `Your score: ${{this.score}}/${{this.questions.length}} (${{percentage.toFixed(1)}}%)`;
        
        // Show retry button
        document.getElementById('retry-btn').classList.add('show');
        
        // Announce results to screen readers
        scoreDisplay.setAttribute('aria-live', 'polite');
        
        if (percentage >= 70) {{
            scoreDisplay.textContent += ' - Excellent work!';
        }} else if (percentage >= 50) {{
            scoreDisplay.textContent += ' - Good effort!';
        }} else {{
            scoreDisplay.textContent += ' - Keep practicing!';
        }}
    }}
    
    retryQuiz() {{
        this.currentQuestion = 0;
        this.score = 0;
        this.userAnswers = new Array(this.questions.length).fill(null);
        
        // Reset UI
        document.querySelectorAll('.question').forEach(q => q.classList.remove('active'));
        document.querySelectorAll('.feedback').forEach(f => {{
            f.style.display = 'none';
            f.className = 'feedback';
        }});
        
        document.getElementById('retry-btn').classList.remove('show');
        document.getElementById('score-display').textContent = '';
        
        this.showQuestion(0);
        this.updateProgress();
    }}
}}

// Initialize quiz when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {{
    new InteractiveQuiz();
}});
        """.strip()
    
    def _create_svg_infographic(self, sections: List[Dict[str, Any]], style: str) -> str:
        """Create SVG infographic"""
        # Simple implementation
        width = 800
        height = 600 + len(sections) * 100  # Dynamic height based on sections
        
        svg_parts = [
            f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg' role='img' aria-labelledby='infographic-title'>",
            f"<title id='infographic-title'>Interactive Infographic</title>"
        ]
        
        # Add background
        svg_parts.append(f"<rect x='0' y='0' width='{width}' height='{height}' fill='#f8f9fa'/>")
        
        # Add sections
        y_position = 50
        colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe']
        
        for i, section in enumerate(sections):
            color = colors[i % len(colors)]
            
            # Section background
            svg_parts.append(
                f"<rect x='50' y='{y_position}' width='{width-100}' height='80' "
                f"fill='{color}' rx='10' ry='10'/>"
            )
            
            # Section content
            title = section.get('title', f'Section {i+1}')
            content = section.get('content', '')
            
            svg_parts.append(
                f"<text x='75' y='{y_position + 25}' font-size='16' font-weight='bold' fill='white'>"
                f"{title}</text>"
            )
            
            svg_parts.append(
                f"<text x='75' y='{y_position + 50}' font-size='14' fill='white'>"
                f"{content}</text>"
            )
            
            y_position += 100
        
        svg_parts.append("</svg>")
        
        return '\n'.join(svg_parts)
    
    def _create_infographic_html(self, svg_content: str, sections: List[Dict[str, Any]]) -> str:
        """Create HTML wrapper for infographic"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Infographic</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .infographic-container {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            max-width: 900px;
            margin: 0 auto;
        }}
        .infographic-title {{
            text-align: center;
            font-size: 2rem;
            margin-bottom: 30px;
            color: #333;
        }}
        svg {{
            width: 100%;
            height: auto;
        }}
        .navigation {{
            text-align: center;
            margin-top: 20px;
        }}
        .nav-btn {{
            padding: 10px 20px;
            margin: 0 10px;
            border: none;
            border-radius: 6px;
            background: #667eea;
            color: white;
            cursor: pointer;
            transition: background 0.3s ease;
        }}
        .nav-btn:hover {{
            background: #5a6fd8;
        }}
    </style>
</head>
<body>
    <div class="infographic-container">
        <h1 class="infographic-title">Interactive Infographic</h1>
        {svg_content}
        <div class="navigation">
            <button class="nav-btn" onclick="scrollToSection('top')">Back to Top</button>
            <button class="nav-btn" onclick="scrollToSection('bottom')">Go to Bottom</button>
        </div>
    </div>
</body>
</html>
        """.strip()
    
    def _create_infographic_interactivity(self, sections: List[Dict[str, Any]]) -> str:
        """Create JavaScript for infographic interactivity"""
        return """
// Infographic Interactivity
function scrollToSection(direction) {
    const container = document.querySelector('.infographic-container');
    if (direction === 'top') {
        container.scrollIntoView({ behavior: 'smooth' });
    } else if (direction === 'bottom') {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }
}

// Add hover effects to SVG elements
document.addEventListener('DOMContentLoaded', function() {
    const svgElements = document.querySelectorAll('svg rect');
    
    svgElements.forEach((element, index) => {
        element.addEventListener('mouseenter', function() {
            this.style.opacity = '0.8';
            this.style.transform = 'scale(1.02)';
            this.style.transition = 'all 0.3s ease';
        });
        
        element.addEventListener('mouseleave', function() {
            this.style.opacity = '1';
            this.style.transform = 'scale(1)';
        });
        
        // Keyboard accessibility
        element.setAttribute('tabindex', '0');
        element.addEventListener('focus', function() {
            this.style.outline = '2px solid #333';
            this.style.outlineOffset = '2px';
        });
        
        element.addEventListener('blur', function() {
            this.style.outline = 'none';
        });
    });
    
    // Add scroll animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    // Apply animation to sections
    document.querySelectorAll('svg rect').forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'all 0.6s ease';
        observer.observe(section);
    });
});
        """.strip()
    
    def _create_component_template(self, component_name: str, template: str) -> str:
        """Create HTML template for web component"""
        return f"""
<!-- {component_name} Web Component Template -->
<template id="{component_name}-template">
    <style>
        :host {{
            display: block;
            font-family: Arial, sans-serif;
        }}
        
        .component-container {{
            padding: 20px;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            background: white;
        }}
        
        .component-title {{
            font-size: 1.5rem;
            margin-bottom: 10px;
            color: #333;
        }}
        
        .component-content {{
            color: #666;
            line-height: 1.6;
        }}
    </style>
    
    <div class="component-container">
        <h2 class="component-title"></h2>
        <div class="component-content"></div>
    </div>
</template>
        """.strip()
    
    def _create_component_css(self, component_name: str, styles: str) -> str:
        """Create CSS for web component"""
        return f"""
/* {component_name} Component Styles */
:host {{
    display: block;
    --component-primary-color: #667eea;
    --component-secondary-color: #764ba2;
    --component-border-radius: 8px;
    --component-padding: 20px;
}}

.component-container {{
    padding: var(--component-padding);
    border: 1px solid #e9ecef;
    border-radius: var(--component-border-radius);
    background: white;
    transition: box-shadow 0.3s ease;
}}

.component-container:hover {{
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}}

.component-title {{
    font-size: 1.5rem;
    margin-bottom: 10px;
    color: var(--component-primary-color);
}}

.component-content {{
    color: #666;
    line-height: 1.6;
}}

/* Accessibility */
:host(:focus-within) .component-container {{
    outline: 2px solid var(--component-primary-color);
    outline-offset: 2px;
}}
        """.strip()
    
    def _create_component_js(self, component_name: str, script: str) -> str:
        """Create JavaScript for web component"""
        return f"""
// {component_name} Web Component
class {component_name.replace('-', '').replace('_', '').title()}Component extends HTMLElement {{
    constructor() {{
        super();
        this.attachShadow({{ mode: 'open' }});
        
        // Clone template
        const template = document.getElementById('{component_name}-template');
        const templateContent = template.content.cloneNode(true);
        this.shadowRoot.appendChild(templateContent);
        
        this.titleElement = this.shadowRoot.querySelector('.component-title');
        this.contentElement = this.shadowRoot.querySelector('.component-content');
    }}
    
    static get observedAttributes() {{
        return ['title', 'content'];
    }}
    
    attributeChangedCallback(name, oldValue, newValue) {{
        if (oldValue !== newValue) {{
            this.render();
        }}
    }}
    
    connectedCallback() {{
        this.render();
        this.addEventListeners();
    }}
    
    render() {{
        const title = this.getAttribute('title') || 'Default Title';
        const content = this.getAttribute('content') || 'Default content goes here.';
        
        if (this.titleElement) {{
            this.titleElement.textContent = title;
        }}
        
        if (this.contentElement) {{
            this.contentElement.textContent = content;
        }}
    }}
    
    addEventListeners() {{
        // Add keyboard support
        this.addEventListener('keydown', (e) => {{
            if (e.key === 'Enter' || e.key === ' ') {{
                e.preventDefault();
                this.dispatchEvent(new CustomEvent('component-activated', {{
                    bubbles: true,
                    composed: true
                }}));
            }}
        }});
        
        // Add click support
        this.addEventListener('click', () => {{
            this.dispatchEvent(new CustomEvent('component-clicked', {{
                bubbles: true,
                composed: true
            }}));
        }});
    }}
    
    // Public methods
    updateTitle(newTitle) {{
        this.setAttribute('title', newTitle);
    }}
    
    updateContent(newContent) {{
        this.setAttribute('content', newContent);
    }}
}}

// Register component
customElements.define('{component_name}', {component_name.replace('-', '').replace('_', '').title()}Component);
        """.strip()
    
    async def _add_aria_attributes(self, html_content: str, content_type: str) -> str:
        """Add ARIA attributes for accessibility"""
        # Simple ARIA enhancement
        enhanced_html = html_content
        
        # Add main landmark
        if '<main>' not in enhanced_html and '<div class="main">' not in enhanced_html:
            enhanced_html = enhanced_html.replace(
                '<body>',
                '<body>\n    <main role="main">'
            ).replace(
                '</body>',
                '    </main>\n</body>'
            )
        
        # Add skip link
        skip_link = '<a href="#main" class="skip-link">Skip to main content</a>'
        enhanced_html = enhanced_html.replace('<body>', f'<body>\n    {skip_link}')
        
        return enhanced_html
    
    async def _add_svg_accessibility(self, svg_content: str, content_type: str) -> str:
        """Add accessibility attributes to SVG elements"""
        # Ensure SVG has proper accessibility attributes
        if 'role="img"' not in svg_content:
            svg_content = svg_content.replace(
                '<svg',
                '<svg role="img"'
            )
        
        if 'aria-labelledby=' not in svg_content:
            svg_content = svg_content.replace(
                '<svg',
                '<svg aria-labelledby="svg-title svg-desc"'
            )
        
        return svg_content
    
    async def _add_keyboard_navigation(self, js_content: str, content_type: str) -> str:
        """Add keyboard navigation support"""
        # Simple keyboard navigation enhancement
        keyboard_nav = """
// Enhanced keyboard navigation
document.addEventListener('keydown', function(e) {
    const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (e.key === 'Tab') {
        // Ensure proper tab order
        focusableElements.forEach((element, index) => {
            element.setAttribute('data-tab-index', index);
        });
    }
    
    if (e.key === 'Escape') {
        // Close modals or reset focus
        document.activeElement.blur();
    }
});
        """
        
        return js_content + '\n\n' + keyboard_nav
    
    async def _analyze_content_structure(self, content: str, content_type: str) -> Dict[str, Any]:
        """Analyze structure of interactive content"""
        analysis = {
            'has_proper_headings': bool(re.search(r'<h[1-6]', content, re.IGNORECASE)),
            'has_landmarks': bool(re.search(r'<main|<nav|<aside|<section|<header|<footer', content, re.IGNORECASE)),
            'has_form_elements': bool(re.search(r'<form|<input|<select|<textarea', content, re.IGNORECASE)),
            'has_interactive_elements': bool(re.search(r'<button|<a|<input', content, re.IGNORECASE)),
            'html_validation': self._validate_html_structure(content),
            'complexity_score': min(1.0, len(content) / 10000)  # Simple complexity metric
        }
        
        return analysis
    
    def _validate_html_structure(self, content: str) -> Dict[str, Any]:
        """Validate HTML structure"""
        validation_results = {
            'valid_structure': True,
            'errors': [],
            'warnings': []
        }
        
        # Check for common HTML issues
        if not re.search(r'<!DOCTYPE\s+html>', content, re.IGNORECASE):
            validation_results['warnings'].append('Missing DOCTYPE declaration')
        
        if not re.search(r'<html[^>]*lang=', content, re.IGNORECASE):
            validation_results['warnings'].append('Missing lang attribute on html element')
        
        if not re.search(r'<meta[^>]*charset', content, re.IGNORECASE):
            validation_results['warnings'].append('Missing charset meta tag')
        
        if not re.search(r'<title>', content, re.IGNORECASE):
            validation_results['errors'].append('Missing title element')
        
        validation_results['valid_structure'] = len(validation_results['errors']) == 0
        
        return validation_results
    
    async def _analyze_accessibility(self, content: str) -> Dict[str, Any]:
        """Analyze accessibility of interactive content"""
        analysis = {
            'has_aria_labels': bool(re.search(r'aria-label=', content)),
            'has_aria_describedby': bool(re.search(r'aria-describedby=', content)),
            'has_alt_attributes': bool(re.search(r'<img[^>]*alt=', content, re.IGNORECASE)),
            'has_form_labels': bool(re.search(r'<label[^>]*for=', content, re.IGNORECASE)),
            'has_keyboard_support': bool(re.search(r'keydown|keypress|keyup', content, re.IGNORECASE)),
            'has_focus_management': bool(re.search(r'focus|blur', content, re.IGNORECASE)),
            'accessibility_score': 0.0,
            'wcag_compliance_level': 'A'  # Minimum compliance level
        }
        
        # Calculate accessibility score
        score_factors = [
            analysis['has_aria_labels'],
            analysis['has_aria_describedby'],
            analysis['has_alt_attributes'],
            analysis['has_form_labels'],
            analysis['has_keyboard_support'],
            analysis['has_focus_management']
        ]
        
        analysis['accessibility_score'] = sum(score_factors) / len(score_factors)
        
        # Determine WCAG compliance level
        if analysis['accessibility_score'] >= 0.8:
            analysis['wcag_compliance_level'] = 'AA'
        elif analysis['accessibility_score'] >= 0.6:
            analysis['wcag_compliance_level'] = 'A'
        else:
            analysis['wcag_compliance_level'] = 'Non-compliant'
        
        return analysis
    
    async def _analyze_interactive_elements(self, content: str) -> List[Dict[str, Any]]:
        """Analyze interactive elements in content"""
        elements = []
        
        # Find interactive elements
        button_pattern = r'<button[^>]*>(.*?)</button>'
        link_pattern = r'<a[^>]*href=[\'"]([^\'"]*)[\'"][^>]*>(.*?)</a>'
        input_pattern = r'<input[^>]*type=[\'"]([^\'"]*)[\'"][^>]*>'
        
        buttons = re.findall(button_pattern, content, re.IGNORECASE | re.DOTALL)
        for button in buttons:
            elements.append({
                'type': 'button',
                'content': button.strip(),
                'accessibility_role': 'button'
            })
        
        links = re.findall(link_pattern, content, re.IGNORECASE | re.DOTALL)
        for href, text in links:
            elements.append({
                'type': 'link',
                'href': href,
                'content': text.strip(),
                'accessibility_role': 'link'
            })
        
        inputs = re.findall(input_pattern, content, re.IGNORECASE)
        for input_type in inputs:
            elements.append({
                'type': 'input',
                'input_type': input_type,
                'accessibility_role': input_type
            })
        
        return elements
    
    async def _analyze_performance(self, content: str) -> Dict[str, Any]:
        """Analyze performance characteristics"""
        # Simple performance metrics
        content_size = len(content)
        
        analysis = {
            'content_size_bytes': content_size,
            'content_size_kb': round(content_size / 1024, 2),
            'estimated_load_time': round(content_size / 1024 / 100, 2),  # Assume 100KB/s
            'complexity_rating': self._rate_content_complexity(content),
            'optimization_suggestions': []
        }
        
        # Generate optimization suggestions
        if content_size > 50000:  # 50KB
            analysis['optimization_suggestions'].append('Consider minifying CSS and JavaScript')
        
        if len(re.findall(r'<script', content, re.IGNORECASE)) > 5:
            analysis['optimization_suggestions'].append('Consider combining JavaScript files')
        
        if len(re.findall(r'<style', content, re.IGNORECASE)) > 3:
            analysis['optimization_suggestions'].append('Consider combining CSS files')
        
        return analysis
    
    def _rate_content_complexity(self, content: str) -> str:
        """Rate content complexity"""
        js_count = len(re.findall(r'<script', content, re.IGNORECASE))
        css_count = len(re.findall(r'<style', content, re.IGNORECASE))
        html_elements = len(re.findall(r'<[^/][^>]*>', content))
        
        complexity_score = js_count + css_count + (html_elements / 100)
        
        if complexity_score > 10:
            return 'high'
        elif complexity_score > 5:
            return 'medium'
        else:
            return 'low'
    
    async def _assess_content_quality(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall content quality"""
        structure = analysis_results.get('structure_analysis', {})
        accessibility = analysis_results.get('accessibility_analysis', {})
        performance = analysis_results.get('performance_analysis', {})
        
        quality_metrics = {
            'structure_score': 0.8 if structure.get('valid_structure', False) else 0.4,
            'accessibility_score': accessibility.get('accessibility_score', 0.0),
            'performance_score': 0.9 if performance.get('complexity_rating') == 'low' else 0.6,
            'overall_quality': 0.0
        }
        
        # Calculate overall quality
        quality_metrics['overall_quality'] = (
            quality_metrics['structure_score'] * 0.3 +
            quality_metrics['accessibility_score'] * 0.4 +
            quality_metrics['performance_score'] * 0.3
        )
        
        return quality_metrics
    
    async def _generate_content_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        accessibility = analysis_results.get('accessibility_analysis', {})
        structure = analysis_results.get('structure_analysis', {})
        performance = analysis_results.get('performance_analysis', {})
        
        # Accessibility recommendations
        if not accessibility.get('has_aria_labels'):
            recommendations.append('Add ARIA labels to interactive elements for better accessibility')
        
        if not accessibility.get('has_alt_attributes'):
            recommendations.append('Add alt attributes to images for screen reader users')
        
        if not accessibility.get('has_keyboard_support'):
            recommendations.append('Ensure all interactive elements support keyboard navigation')
        
        # Structure recommendations
        if not structure.get('has_proper_headings'):
            recommendations.append('Use proper heading hierarchy (H1-H6) for better content structure')
        
        if not structure.get('has_landmarks'):
            recommendations.append('Add semantic landmarks (main, nav, aside, etc.) for better navigation')
        
        # Performance recommendations
        for suggestion in performance.get('optimization_suggestions', []):
            recommendations.append(suggestion)
        
        # General recommendations
        if len(recommendations) == 0:
            recommendations.append('Content quality is good. Consider adding more interactive features.')
        
        return recommendations
    
    async def _generate_accessible_element(
        self,
        element_type: str,
        content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate an accessible interactive element"""
        element_config = self.element_types.get(element_type, {})
        
        if not element_config:
            raise ValueError(f"Unsupported element type: {element_type}")
        
        # Generate basic element
        element = {
            'type': element_type,
            'content': content,
            'attributes': {
                'role': element_config['accessibility_role'],
                'aria-label': context.get('label', f'{element_type} element')
            }
        }
        
        # Add type-specific attributes
        if element_type == 'button':
            element['attributes']['type'] = 'button'
            if context.get('disabled'):
                element['attributes']['disabled'] = 'true'
        
        elif element_type == 'input':
            element['attributes']['type'] = context.get('input_type', 'text')
            if context.get('placeholder'):
                element['attributes']['placeholder'] = context['placeholder']
            if context.get('required'):
                element['attributes']['aria-required'] = 'true'
        
        return element
    
    async def _add_accessibility_attributes(
        self,
        element: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add comprehensive accessibility attributes to element"""
        # Ensure all required attributes are present
        element_type = element['type']
        required_attrs = self.element_types.get(element_type, {}).get('required_attributes', [])
        
        for attr in required_attrs:
            if attr not in element['attributes']:
                if attr == 'aria-label':
                    element['attributes'][attr] = context.get('label', f'{element_type} element')
                elif attr == 'placeholder':
                    element['attributes'][attr] = context.get('placeholder', '')
                elif attr == 'alt':
                    element['attributes'][attr] = context.get('alt', 'Image element')
        
        # Add additional accessibility enhancements
        if context.get('description'):
            element['attributes']['aria-describedby'] = context['description']
        
        if context.get('error_message'):
            element['attributes']['aria-invalid'] = 'true'
            element['attributes']['aria-describedby'] = context.get('error_id', 'error-message')
        
        if context.get('expanded') is not None:
            element['attributes']['aria-expanded'] = str(context['expanded']).lower()
        
        if context.get('selected') is not None:
            element['attributes']['aria-selected'] = str(context['selected']).lower()
        
        return element
    
    async def _test_screen_reader_compatibility(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Test screen reader compatibility (mock implementation)"""
        # Mock screen reader testing
        compatibility_score = 0.0
        recommendations = []
        
        attributes = element.get('attributes', {})
        
        # Check for essential accessibility attributes
        if 'aria-label' in attributes:
            compatibility_score += 0.3
        else:
            recommendations.append('Add aria-label for screen reader identification')
        
        if element['type'] == 'img' and 'alt' in attributes:
            compatibility_score += 0.3
        elif element['type'] != 'img' and 'role' in attributes:
            compatibility_score += 0.2
        else:
            recommendations.append('Add appropriate role attribute')
        
        if 'aria-describedby' in attributes or not recommendations:
            compatibility_score += 0.2
        
        if 'tabindex' in attributes:
            compatibility_score += 0.2
        
        # Additional checks
        if element['type'] in ['button', 'input'] and 'disabled' in attributes:
            compatibility_score += 0.1
        
        return {
            'score': compatibility_score,
            'compatible': compatibility_score >= 0.7,
            'recommendations': recommendations
        }
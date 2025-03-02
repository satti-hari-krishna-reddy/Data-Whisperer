from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.shapes.shapetree import SlideShapes
import io
import re
import datetime

from utils import get_gemini_response

def clean_ai_text(text: str) -> str:
    """
    Removes weird ASCII control characters, all asterisks (*), and backticks (`).
    Preserves normal punctuation, newlines, and other symbols.

    Steps:
      1) Strip ASCII control chars [\x00-\x08, \x0B-\x0C, \x0E-\x1F, \x7F-\x9F].
      2) Remove carriage returns (\r).
      3) Collapse multiple blank lines into one.
      4) Remove all asterisks (*) and backticks (`).
      5) Trim leading/trailing whitespace.
    """
    # 1. Remove control chars
    cleaned = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    
    # 2. Remove carriage returns
    cleaned = cleaned.replace('\r', '')
    
    # 3. Collapse multiple blank lines
    cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
    
    # 4. Remove asterisks and backticks
    cleaned = re.sub(r'[`*]', '', cleaned)
    
    # 5. Trim whitespace
    cleaned = cleaned.strip()
    
    return cleaned

def generate_eda_report_ppt(
    eda_metadata,
    df,
    numeric_figs=None,
    categorical_figs=None,
    correlation_figs=None,
    time_series_figs=None,
    outlier_figs=None,
    dataset_name="Dataset.csv"
):
    """
    Generates a PPTX report with a dark background and white text,
    splitting commentary by both line count (max ~22 lines) and word count (max ~300 words).
    If either limit is exceeded, we start a new slide.

    1) Title slide (dark background).
    2) Overview slide (rows, columns).
    3) Per-section commentary + figure slides.
    4) Graceful kaleido error handling for figures.
    5) Conclusion.

    Returns a BytesIO with the PPTX content.
    """

    # Convert None to empty lists
    numeric_figs = numeric_figs or []
    categorical_figs = categorical_figs or []
    correlation_figs = correlation_figs or []
    time_series_figs = time_series_figs or []
    outlier_figs = outlier_figs or []

    numeric_insights = get_gemini_response(f""" Here is the dataset context (in JSON):
                                            {eda_metadata}

                                            INSTRUCTIONS:
                                            - Summarize the **numeric columns** in a friendly, user-focused way.
                                            - Write about 150 to 250 words total.
                                            - Use plain text only—no code blocks, no triple backticks, no excessive Markdown.
                                            - Organize the summary in **bullet points** (1–2 lines each).
                                            - For each bullet, give a short explanation suitable for **non-technical** users.
                                            - Include each numeric column’s typical range, average, or any key outliers or patterns.
                                            - If the dataset has no numeric columns, say “No numeric columns found.”
                                            - Output must be the **final text only** no formatting.
                                            """)
    categorical_insights = get_gemini_response(f""" Here is the dataset context (in JSON):
                                            {eda_metadata}

                                            INSTRUCTIONS:
                                            - Summarize the **categorical columns** in a friendly, user-focused way.
                                            - Write about 150 to 250 words total.
                                            - Use plain text only—no code blocks, no triple backticks, no excessive Markdown.
                                            - Organize the summary in **bullet points** (1–2 lines each).
                                            - For each bullet, give a short explanation suitable for **non-technical** users.
                                            - Include each numeric column’s typical range, average, or any key outliers or patterns.
                                            - If the dataset has no categorical columns, say “No categorical columns found.”
                                            - Output must be the **final text only** no formatting.
                                            """)
    correlation_insights = get_gemini_response(f""" Here is the dataset context (in JSON):
                                            {eda_metadata}

                                            INSTRUCTIONS:
                                            - Summarize the **correlation columns** in a friendly, user-focused way.
                                            - Write about 150 to 250 words total.
                                            - Use plain text only—no code blocks, no triple backticks, no excessive Markdown.
                                            - Organize the summary in **bullet points** (1–2 lines each).
                                            - For each bullet, give a short explanation suitable for **non-technical** users.
                                            - Include each numeric column’s typical range, average, or any key outliers or patterns.
                                            - If the dataset has no correlation columns, say “No correlation columns found.”
                                            - Output must be the **final text only** no formatting.
                                            """)
    outlier_insights = get_gemini_response(f""" Here is the dataset context (in JSON):
                                            {eda_metadata}

                                            INSTRUCTIONS:
                                            - Summarize the **outliners columns** in a friendly, user-focused way.
                                            - Write about 150 to 250 words total.
                                            - Use plain text only—no code blocks, no triple backticks, no excessive Markdown.
                                            - Organize the summary in **bullet points** (1–2 lines each).
                                            - For each bullet, give a explanation suitable for **non-technical** users.
                                            - Include each numeric column’s typical range, average, or any key outliers or patterns.
                                            - If the dataset has no outliners columns, say “No outliners columns found.”
                                            - Output must be the **final text only** no formatting.
                                            """)
    time_series_insights = get_gemini_response(f""" Here is the dataset context (in JSON):
                                            {eda_metadata}

                                            INSTRUCTIONS:
                                            - Summarize the **time series columns** in a friendly, user-focused way.
                                            - Write about 150 to 250 words total.
                                            - Use plain text only—no code blocks, no triple backticks, no excessive Markdown.
                                            - Organize the summary in **bullet points** (1–2 lines each).
                                            - For each bullet, give a short explanation suitable for **non-technical** users.
                                            - Include each numeric column’s typical range, average, or any key outliers or patterns.
                                            - If the dataset has no time series columns, say “No time series columns found.”
                                            - Output must be the **final text only** no formatting.
                                            """)
    overall_insights = get_gemini_response(f"""Here is the dataset context (in JSON):
                                            {eda_metadata}

                                            INSTRUCTIONS:
                                            - Provide an **depth summary** of the entire EDA in a friendly, user-focused way and breif enough.
                                            - Use plain text only—no code blocks, no triple backticks, no excessive Markdown.
                                            - Focus on **actionable insights**, key findings, or interesting patterns across numeric, categorical, correlation, or time-series data.
                                            - Avoid repeating trivial details; highlight the big takeaways that **non-technical** readers can understand.
                                            - Output must be the **final text only**, no formatting.
                                            """)
    
    # Clean AI-generated text
    numeric_insights = clean_ai_text(numeric_insights)
    categorical_insights = clean_ai_text(categorical_insights)
    correlation_insights = clean_ai_text(correlation_insights)
    outlier_insights = clean_ai_text(outlier_insights)
    time_series_insights = clean_ai_text(time_series_insights)
    overall_insights = clean_ai_text(overall_insights)



    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    def add_dark_slide(prs):
        """Add dark-themed slide with proper background"""
        slide_layout = prs.slide_layouts[6]  # Blank layout
        slide = prs.slides.add_slide(slide_layout)
        shapes: SlideShapes = slide.shapes
        bg_shape = shapes.add_shape(
            1,  # Rectangle
            0, 0, 
            prs.slide_width, prs.slide_height
        )
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = RGBColor(26, 42, 58)  # Dark blue
        bg_shape.line.fill.background()
        return slide

    def add_textbox(slide, left, top, width, height, text, 
                   font_size=24, color=RGBColor(250,250,250),
                   align=PP_ALIGN.LEFT, bold=False, font_name='Calibri'):
        """Add properly formatted textbox"""
        box = slide.shapes.add_textbox(left, top, width, height)
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.alignment = align
        
        # Set font properties
        font = p.font
        font.size = Pt(font_size)
        font.color.rgb = color
        font.bold = bold
        font.name = font_name
        
        return box

    def chunk_text_spatially(text, max_lines=18, max_words=140, max_height=5.5):
        """Split text considering lines, words, and visual height"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_lines = 0
        current_words = 0

        for line in lines:
            line_words = len(line.split())
            line_height = 0.3  # ~14pt font height
            
            if (current_lines + 1 > max_lines or
                current_words + line_words > max_words or
                len(current_chunk)*line_height > max_height):
                
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_lines = 1
                current_words = line_words
            else:
                current_chunk.append(line)
                current_lines += 1
                current_words += line_words

        if current_chunk:
            chunks.append("\n".join(current_chunk))
        return chunks

    def add_section(section_title, commentary_text, figs):
        """Add section with commentary and figures"""
        if not commentary_text.strip():
            return
            
        chunks = chunk_text_spatially(commentary_text)
        for idx, chunk in enumerate(chunks):
            slide = add_dark_slide(prs)
            
            # Title
            add_textbox(
                slide,
                Inches(0.7), Inches(0.5),
                Inches(11.5), Inches(0.6),
                text=section_title if idx == 0 else f"{section_title} (cont.)",
                font_size=28,
                bold=True,
                font_name='Calibri Bold'
            )
            
            # Content
            add_textbox(
                slide,
                Inches(0.7), Inches(1.5),
                Inches(11.5), Inches(5.0),
                text=chunk,
                font_size=16,
                font_name='Calibri',
                align=PP_ALIGN.LEFT
            )
            
        for i, fig in enumerate(figs):
            slide = add_dark_slide(prs)
            
            # Figure title
            add_textbox(
                slide,
                Inches(0.7), Inches(0.5),
                Inches(11.5), Inches(0.6),
                text=f"{section_title} - Figure {i+1}",
                font_size=24,
                bold=True,
                font_name='Calibri Bold'
            )
            
            # Figure image
            try:
                img_bytes = fig.to_image(format="png", scale=2)
                pic = slide.shapes.add_picture(
                    io.BytesIO(img_bytes),
                    left=Inches(0.7),
                    top=Inches(1.5),
                    width=Inches(11.5),
                    height=Inches(5.0)
                )
                pic.width = Inches(11.5)
                pic.height = Inches(5.0)
            except Exception as e:
                add_textbox(
                    slide,
                    Inches(0.7), Inches(1.5),
                    Inches(11.5), Inches(5.0),
                    text=f"Error rendering figure: {str(e)}",
                    font_size=16,
                    color=RGBColor(255, 0, 0)
                )

    # Title slide
    title_slide = add_dark_slide(prs)
    add_textbox(
        title_slide,
        Inches(0.5), Inches(1.5),
        Inches(12), Inches(1.0),
        text="EDA Analysis Report",
        font_size=44,
        bold=True,
        font_name='Calibri Bold',
        align=PP_ALIGN.LEFT
    )
    add_textbox(
        title_slide,
        Inches(0.5), Inches(2.8),
        Inches(12), Inches(0.6),
        text=f"Dataset: {dataset_name}\nGenerated: {datetime.datetime.now():%B %d, %Y}",
        font_size=18,
        font_name='Calibri Light',
        align=PP_ALIGN.LEFT
    )

    # Dataset overview
    overview_slide = add_dark_slide(prs)
    add_textbox(
        overview_slide,
        Inches(0.7), Inches(0.5),
        Inches(11.5), Inches(0.6),
        text="Dataset Overview",
        font_size=28,
        bold=True,
        font_name='Calibri Bold'
    )
    
    overview_text = f"Rows: {df.shape[0]}\nColumns: {df.shape[1]}"
    if eda_metadata.get("columns"):
        overview_text += "\n\nColumns:\n• " + "\n• ".join(eda_metadata["columns"].keys())
        
    add_textbox(
        overview_slide,
        Inches(0.7), Inches(1.5),
        Inches(11.5), Inches(5.0),
        text=overview_text,
        font_size=16,
        font_name='Calibri'
    )

    # Add analysis sections
    add_section("Numeric Analysis", numeric_insights, numeric_figs)
    add_section("Categorical Analysis", categorical_insights, categorical_figs)
    add_section("Correlation Analysis", correlation_insights, correlation_figs)
    add_section("Time Series Analysis", time_series_insights, time_series_figs)
    add_section("Outlier Analysis", outlier_insights, outlier_figs)

    # Conclusion
    conclusion_slide = add_dark_slide(prs)
    add_textbox(
        conclusion_slide,
        Inches(0.7), Inches(0.5),
        Inches(11.5), Inches(0.6),
        text="Conclusion",
        font_size=28,
        bold=True,
        font_name='Calibri Bold'
    )
    add_textbox(
        conclusion_slide,
        Inches(0.7), Inches(1.5),
        Inches(11.5), Inches(5.0),
        text="• Analysis successfully completed\n• Key insights highlighted\n• Next steps recommended",
        font_size=18,
        font_name='Calibri'
    )

    # Save to buffer
    ppt_buffer = io.BytesIO()
    prs.save(ppt_buffer)
    ppt_buffer.seek(0)
    return ppt_buffer

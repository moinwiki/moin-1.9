/*
 * @(#)SVGTextArea.java
 *
 * Copyright (c) 1996-2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.samples.svg.figures;

import java.awt.*;
import java.awt.font.*;
import java.awt.geom.*;
import java.text.*;
import java.util.*;
import static org.jhotdraw.samples.svg.SVGAttributeKeys.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.samples.svg.*;
import org.jhotdraw.geom.*;

/**
 * SVGTextArea.
 *
 * @author Werner Randelshofer
 * @version $Id: SVGTextAreaFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class SVGTextAreaFigure extends SVGAttributedFigure
        implements SVGFigure, TextHolderFigure {

    private Rectangle2D.Double bounds = new Rectangle2D.Double();
    private boolean editable = true;
    private final static BasicStroke dashes = new BasicStroke(1f, BasicStroke.CAP_BUTT, BasicStroke.JOIN_BEVEL, 0f, new float[]{4f, 4f}, 0f);
    /**
     * This is a cached value to improve the performance of method isTextOverflow();
     */
    private Boolean isTextOverflow;
    /**
     * This is used to perform faster drawing and hit testing.
     */
    private transient Rectangle2D.Double cachedDrawingArea;
    private transient Shape cachedTextShape;

    /** Creates a new instance. */
    public SVGTextAreaFigure() {
        this("Text");
    }

    public SVGTextAreaFigure(String text) {
        setText(text);
        SVGAttributeKeys.setDefaults(this);
    }
    // DRAWING

    @Override
    protected void drawText(java.awt.Graphics2D g) {
    }

    protected void drawFill(Graphics2D g) {
        g.fill(getTextShape());
        g.draw(new Rectangle2D.Double(getBounds().x, getBounds().y, getPreferredTextSize(changingDepth).width, getPreferredTextSize(changingDepth).height));
    }

    protected void drawStroke(Graphics2D g) {
        g.draw(getTextShape());
    }
    // SHAPE AND BOUNDS

    public Rectangle2D.Double getBounds() {
        return (Rectangle2D.Double) bounds.clone();
    }

    @Override
    public Rectangle2D.Double getDrawingArea() {
        if (cachedDrawingArea == null) {
            Rectangle2D rx = getBounds();
            Rectangle2D.Double r = (rx instanceof Rectangle2D.Double) ? (Rectangle2D.Double) rx : new Rectangle2D.Double(rx.getX(), rx.getY(), rx.getWidth(), rx.getHeight());
            double g = SVGAttributeKeys.getPerpendicularHitGrowth(this);
            Geom.grow(r, g, g);
            if (TRANSFORM.get(this) == null) {
                cachedDrawingArea = r;
            } else {
                cachedDrawingArea = new Rectangle2D.Double();
                cachedDrawingArea.setRect(TRANSFORM.get(this).createTransformedShape(r).getBounds2D());
            }
        }
        return (Rectangle2D.Double) cachedDrawingArea.clone();
    }

    /**
     * Checks if a Point2D.Double is inside the figure.
     */
    public boolean contains(Point2D.Double p) {
        if (TRANSFORM.get(this) != null) {
            try {
                p = (Point2D.Double) TRANSFORM.get(this).inverseTransform(p, new Point2D.Double());
            } catch (NoninvertibleTransformException ex) {
                ex.printStackTrace();
            }
        }

        Rectangle2D r = getTextShape().getBounds2D();
        return r.isEmpty() ? getBounds().contains(p) : r.contains(p);
    }

    private Shape getTextShape() {
        if (cachedTextShape == null) {
            GeneralPath shape;
            cachedTextShape = shape = new GeneralPath();
            if (getText() != null || isEditable()) {

                Font font = getFont();
                boolean isUnderlined = FONT_UNDERLINE.get(this);
                Insets2D.Double insets = getInsets();
                Rectangle2D.Double textRect = new Rectangle2D.Double(
                        bounds.x + insets.left,
                        bounds.y + insets.top,
                        bounds.width - insets.left - insets.right,
                        bounds.height - insets.top - insets.bottom);
                float leftMargin = (float) textRect.x;
                float rightMargin = (float) Math.max(leftMargin + 1, textRect.x + textRect.width);
                float verticalPos = (float) textRect.y;
                float maxVerticalPos = (float) (textRect.y + textRect.height);
                if (leftMargin < rightMargin) {
                    float tabWidth = (float) (getTabSize() * font.getStringBounds("m", getFontRenderContext()).getWidth());
                    float[] tabStops = new float[(int) (textRect.width / tabWidth)];
                    for (int i = 0; i < tabStops.length; i++) {
                        tabStops[i] = (float) (textRect.x + (int) (tabWidth * (i + 1)));
                    }

                    if (getText() != null) {
                        String[] paragraphs = getText().split("\n");//Strings.split(getText(), '\n');
                        for (int i = 0; i < paragraphs.length; i++) {
                            if (paragraphs[i].length() == 0) {
                                paragraphs[i] = " ";
                            }
                            AttributedString as = new AttributedString(paragraphs[i]);
                            as.addAttribute(TextAttribute.FONT, font);
                            if (isUnderlined) {
                                as.addAttribute(TextAttribute.UNDERLINE, TextAttribute.UNDERLINE_LOW_ONE_PIXEL);
                            }
                            int tabCount = paragraphs[i].split("\t").length - 1;
                            Rectangle2D.Double paragraphBounds = appendParagraph(
                                    shape, as.getIterator(),
                                    verticalPos, maxVerticalPos, leftMargin, rightMargin, tabStops, tabCount);
                            verticalPos = (float) (paragraphBounds.y + paragraphBounds.height);
                            if (verticalPos > textRect.y + textRect.height) {
                                break;
                            }
                        }
                    }
                }
            }
        }
        return cachedTextShape;
    }

    /**
     * Appends a paragraph of text at the specified y location and returns
     * the bounds of the paragraph.
     * 
     *
     * @param shape Shape to which to add the glyphs of the paragraph. This 
     * parameter is null, if we only want to measure the size of the paragraph.
     * @param styledText the text of the paragraph.
     * @param verticalPos the top bound of the paragraph
     * @param maxVerticalPos the bottom bound of the paragraph
     * @param leftMargin the left bound of the paragraph
     * @param rightMargin the right bound of the paragraph
     * @param tabStops an array with tab stops
     * @param tabCounts the number of entries in tabStops which contain actual
     *        values
     * @return Returns the actual bounds of the paragraph.
     */
    private Rectangle2D.Double appendParagraph(GeneralPath shape,
            AttributedCharacterIterator styledText,
            float verticalPos, float maxVerticalPos,
            float leftMargin, float rightMargin,
            float[] tabStops, int tabCount) {

        // assume styledText is an AttributedCharacterIterator, and the number
        // of tabs in styledText is tabCount

        Rectangle2D.Double paragraphBounds = new Rectangle2D.Double(leftMargin, verticalPos, 0, 0);

        int[] tabLocations = new int[tabCount + 1];

        int i = 0;
        for (char c = styledText.first(); c != styledText.DONE; c = styledText.next()) {
            if (c == '\t') {
                tabLocations[i++] = styledText.getIndex();
            }
        }
        tabLocations[tabCount] = styledText.getEndIndex() - 1;

        // Now tabLocations has an entry for every tab's offset in
        // the text.  For convenience, the last entry is tabLocations
        // is the offset of the last character in the text.

        LineBreakMeasurer measurer = new LineBreakMeasurer(styledText, getFontRenderContext());
        int currentTab = 0;

        while (measurer.getPosition() < styledText.getEndIndex()) {

            // Lay out and draw each line.  All segments on a line
            // must be computed before any drawing can occur, since
            // we must know the largest ascent on the line.
            // TextLayouts are computed and stored in a List;
            // their horizontal positions are stored in a parallel
            // List.

            // lineContainsText is true after first segment is drawn
            boolean lineContainsText = false;
            boolean lineComplete = false;
            float maxAscent = 0, maxDescent = 0;
            float horizontalPos = leftMargin;
            LinkedList<TextLayout> layouts = new LinkedList<TextLayout>();
            LinkedList<Float> penPositions = new LinkedList<Float>();

            while (!lineComplete) {
                float wrappingWidth = rightMargin - horizontalPos;
                TextLayout layout = null;
                layout =
                        measurer.nextLayout(wrappingWidth,
                        tabLocations[currentTab] + 1,
                        lineContainsText);

                // layout can be null if lineContainsText is true
                if (layout != null) {
                    layouts.add(layout);
                    penPositions.add(horizontalPos);
                    horizontalPos += layout.getAdvance();
                    maxAscent = Math.max(maxAscent, layout.getAscent());
                    maxDescent = Math.max(maxDescent,
                            layout.getDescent() + layout.getLeading());
                } else {
                    lineComplete = true;
                }

                lineContainsText = true;

                if (measurer.getPosition() == tabLocations[currentTab] + 1) {
                    currentTab++;
                }

                if (measurer.getPosition() == styledText.getEndIndex()) {
                    lineComplete = true;
                } else if (tabStops.length == 0 || horizontalPos >= tabStops[tabStops.length - 1]) {
                    lineComplete = true;
                }
                if (!lineComplete) {
                    // move to next tab stop
                    int j;
                    for (j = 0; horizontalPos >= tabStops[j]; j++) {
                    }
                    horizontalPos = tabStops[j];
                }
            }

            verticalPos += maxAscent;
            if (verticalPos > maxVerticalPos) {
                break;
            }

            Iterator<TextLayout> layoutEnum = layouts.iterator();
            Iterator<Float> positionEnum = penPositions.iterator();

            // now iterate through layouts and draw them
            while (layoutEnum.hasNext()) {
                TextLayout nextLayout = layoutEnum.next();
                float nextPosition = positionEnum.next();
                AffineTransform tx = new AffineTransform();
                tx.translate(nextPosition, verticalPos);
                if (shape != null) {
                    Shape outline = nextLayout.getOutline(tx);
                    shape.append(outline, false);
                }
                Rectangle2D layoutBounds = nextLayout.getBounds();
                paragraphBounds.add(new Rectangle2D.Double(layoutBounds.getX() + nextPosition,
                        layoutBounds.getY() + verticalPos,
                        layoutBounds.getWidth(),
                        layoutBounds.getHeight()));
            }

            verticalPos += maxDescent;
        }

        return paragraphBounds;
    }

    public void setBounds(Point2D.Double anchor, Point2D.Double lead) {
        bounds.x = Math.min(anchor.x, lead.x);
        bounds.y = Math.min(anchor.y, lead.y);
        bounds.width = Math.max(0.1, Math.abs(lead.x - anchor.x));
        bounds.height = Math.max(0.1, Math.abs(lead.y - anchor.y));
        invalidate();
    }

    /**
     * Transforms the figure.
     *
     * @param tx the transformation.
     */
    public void transform(AffineTransform tx) {
        if (TRANSFORM.get(this) != null ||
                (tx.getType() &
                (AffineTransform.TYPE_TRANSLATION /*| AffineTransform.TYPE_MASK_SCALE*/)) !=
                tx.getType()) {
            if (TRANSFORM.get(this) == null) {
                TRANSFORM.basicSet(this, (AffineTransform) tx.clone());
            } else {
                AffineTransform t = TRANSFORM.getClone(this);
                t.preConcatenate(tx);
                TRANSFORM.basicSet(this, t);
            }
        } else {
            Point2D.Double anchor = getStartPoint();
            Point2D.Double lead = getEndPoint();
            setBounds(
                    (Point2D.Double) tx.transform(anchor, anchor),
                    (Point2D.Double) tx.transform(lead, lead));
            if (FILL_GRADIENT.get(this) != null &&
                    !FILL_GRADIENT.get(this).isRelativeToFigureBounds()) {
                Gradient g = FILL_GRADIENT.getClone(this);
                g.transform(tx);
                FILL_GRADIENT.basicSet(this, g);
            }
            if (STROKE_GRADIENT.get(this) != null &&
                    !STROKE_GRADIENT.get(this).isRelativeToFigureBounds()) {
                Gradient g = STROKE_GRADIENT.getClone(this);
                g.transform(tx);
                STROKE_GRADIENT.basicSet(this, g);
            }
        }
        invalidate();
    }

    public void restoreTransformTo(Object geometry) {
        Object[] restoreData = (Object[]) geometry;
        bounds = (Rectangle2D.Double) ((Rectangle2D.Double) restoreData[0]).clone();
        TRANSFORM.basicSetClone(this, (AffineTransform) restoreData[1]);
        FILL_GRADIENT.basicSetClone(this, (Gradient) restoreData[2]);
        STROKE_GRADIENT.basicSetClone(this, (Gradient) restoreData[3]);
        invalidate();
    }

    public Object getTransformRestoreData() {
        return new Object[]{
                    bounds.clone(),
                    TRANSFORM.getClone(this),
                    FILL_GRADIENT.getClone(this),
                    STROKE_GRADIENT.getClone(this),};
    }
// ATTRIBUTES

    public String getText() {
        return (String) getAttribute(TEXT);
    }

    public int getTextColumns() {
        return (getText() == null) ? 4 : Math.max(getText().length(), 4);
    }

    public <T> void setAttribute(AttributeKey<T> key, T newValue) {
        if (key.equals(SVGAttributeKeys.TRANSFORM) ||
                key.equals(SVGAttributeKeys.FONT_FACE) ||
                key.equals(SVGAttributeKeys.FONT_BOLD) ||
                key.equals(SVGAttributeKeys.FONT_ITALIC) ||
                key.equals(SVGAttributeKeys.FONT_SIZE) ||
                key.equals(SVGAttributeKeys.STROKE_WIDTH) ||
                key.equals(SVGAttributeKeys.STROKE_COLOR) ||
                key.equals(SVGAttributeKeys.STROKE_GRADIENT)) {
            invalidate();
        }
        super.setAttribute(key, newValue);
    }

    /**
     * Sets the text shown by the text figure.
     */
    public void setText(String newText) {
        TEXT.set(this, newText);
    }

    /**
     * Returns the insets used to draw text.
     */
    public Insets2D.Double getInsets() {
        double sw = (STROKE_COLOR.get(this) == null) ? 0 : Math.ceil(STROKE_WIDTH.get(this) / 2);
        Insets2D.Double insets = new Insets2D.Double(0, 0, 0, 0);
        return new Insets2D.Double(insets.top + sw, insets.left + sw, insets.bottom + sw, insets.right + sw);
    }

    public double getBaseline() {
        return getFont().getLineMetrics(getText(), getFontRenderContext()).getAscent() + getInsets().top;
    }

    public int getTabSize() {
        return 8;
    }

    public TextHolderFigure getLabelFor() {
        return this;
    }

    public Font getFont() {
        return SVGAttributeKeys.getFont(this);
    }

    public Color getTextColor() {
        return FILL_COLOR.get(this);
    //   return TEXT_COLOR.get(this);
    }

    public Color getFillColor() {
        return FILL_COLOR.get(this).equals(Color.white) ? Color.black : Color.WHITE;
    //  return FILL_COLOR.get(this);
    }

    public void setFontSize(float size) {
        Point2D.Double p = new Point2D.Double(0, size);
        AffineTransform tx = TRANSFORM.get(this);
        if (tx != null) {
            try {
                tx.inverseTransform(p, p);
                Point2D.Double p0 = new Point2D.Double(0, 0);
                tx.inverseTransform(p0, p0);
                p.y -= p0.y;
            } catch (NoninvertibleTransformException ex) {
                ex.printStackTrace();
            }
        }
        FONT_SIZE.set(this, Math.abs(p.y));
    }

    public float getFontSize() {
        Point2D.Double p = new Point2D.Double(0, FONT_SIZE.get(this));
        AffineTransform tx = TRANSFORM.get(this);
        if (tx != null) {
            tx.transform(p, p);
            Point2D.Double p0 = new Point2D.Double(0, 0);
            tx.transform(p0, p0);
            p.y -= p0.y;
        /*
        try {
        tx.inverseTransform(p, p);
        } catch (NoninvertibleTransformException ex) {
        ex.printStackTrace();
        }*/
        }
        return (float) Math.abs(p.y);
    }
// EDITING

    public boolean isEditable() {
        return editable;
    }

    public void setEditable(boolean b) {
        this.editable = b;
    }

    @Override
    public Collection<Handle> createHandles(int detailLevel) {
        LinkedList<Handle> handles = new LinkedList<Handle>();

        switch (detailLevel % 2) {
            case -1: // Mouse hover handles
                handles.add(new BoundsOutlineHandle(this, false, true));
                break;
            case 0:
                ResizeHandleKit.addResizeHandles(this, handles);
                handles.add(new FontSizeHandle(this));
                handles.add(new TextOverflowHandle(this));
                handles.add(new LinkHandle(this));
                break;
            case 1:
                TransformHandleKit.addTransformHandles(this, handles);
                break;
            default:
                break;
        }
        return handles;
    }

    /**
     * Returns a specialized tool for the given coordinate.
     * <p>Returns null, if no specialized tool is available.
     */
    public Tool getTool(Point2D.Double p) {
        if (isEditable() && contains(p)) {
            TextAreaEditingTool tool = new TextAreaEditingTool(this);
            return tool;
        }
        return null;
    }
// CONNECTING

    public boolean canConnect() {
        return false; // SVG does not support connecting
    }

    public Connector findConnector(Point2D.Double p, ConnectionFigure prototype) {
        return null; // SVG does not support connectors
    }

    public Connector findCompatibleConnector(Connector c, boolean isStartConnector) {
        return null; // SVG does not support connectors
    }
// COMPOSITE FIGURES
// CLONING
// EVENT HANDLING

    /**
     * Gets the text shown by the text figure.
     */
    public boolean isEmpty() {
        return getText() == null || getText().length() == 0;
    }

    @Override
    public void invalidate() {
        super.invalidate();
        cachedDrawingArea = null;
        cachedTextShape = null;
        isTextOverflow = null;
    }

    public boolean isTextOverflow() {
        if (isTextOverflow == null) {
            Insets2D.Double insets = getInsets();
            isTextOverflow = getPreferredTextSize(getBounds().width - insets.left - insets.right).height > getBounds().height - insets.top - insets.bottom;
        }
        return isTextOverflow;
    }

    /**
     * Returns the preferred text size of the TextAreaFigure.
     * <p>
     * If you want to use this method to determine the bounds of the TextAreaFigure,
     * you need to add the insets of the TextAreaFigure to the size.
     * 
     * @param maxWidth the maximal width to use. Specify Double.MAX_VALUE
     * if you want the width to be unlimited.
     * @return width and height needed to lay out the text.
     */
    public Dimension2DDouble getPreferredTextSize(double maxWidth) {
        Rectangle2D.Double textRect = new Rectangle2D.Double();
        if (getText() != null) {
            Font font = getFont();
            boolean isUnderlined = FONT_UNDERLINE.get(this);
            float leftMargin = 0;
            float rightMargin = (float) maxWidth - 1;
            float verticalPos = 0;
            float maxVerticalPos = Float.MAX_VALUE;
            if (leftMargin < rightMargin) {
                float tabWidth = (float) (getTabSize() * font.getStringBounds("m", getFontRenderContext()).getWidth());
                float[] tabStops = new float[(int) (textRect.width / tabWidth)];
                for (int i = 0; i < tabStops.length; i++) {
                    tabStops[i] = (float) (textRect.x + (int) (tabWidth * (i + 1)));
                }

                if (getText() != null) {
                    String[] paragraphs = getText().split("\n");//Strings.split(getText(), '\n');

                    for (int i = 0; i < paragraphs.length; i++) {
                        if (paragraphs[i].length() == 0) {
                            paragraphs[i] = " ";
                        }
                        AttributedString as = new AttributedString(paragraphs[i]);
                        as.addAttribute(TextAttribute.FONT, font);
                        if (isUnderlined) {
                            as.addAttribute(TextAttribute.UNDERLINE, TextAttribute.UNDERLINE_LOW_ONE_PIXEL);
                        }
                        int tabCount = paragraphs[i].split("\t").length - 1;
                        Rectangle2D.Double paragraphBounds = appendParagraph(null, as.getIterator(), verticalPos, maxVerticalPos, leftMargin, rightMargin, tabStops, tabCount);
                        verticalPos = (float) (paragraphBounds.y + paragraphBounds.height);
                        textRect.add(paragraphBounds);
                    }
                }
            }
        }
        return new Dimension2DDouble(Math.abs(textRect.x) + textRect.width, Math.abs(textRect.y) + textRect.height);
    }

    public SVGTextAreaFigure clone() {
        SVGTextAreaFigure that = (SVGTextAreaFigure) super.clone();
        that.bounds = (Rectangle2D.Double) this.bounds.clone();
        return that;
    }
}


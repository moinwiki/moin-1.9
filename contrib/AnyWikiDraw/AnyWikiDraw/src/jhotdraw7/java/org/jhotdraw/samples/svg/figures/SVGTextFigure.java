/*
 * @(#)SVGText.java
 *
 * Copyright (c) 1996-2008 by the original authors of JHotDraw
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
import java.awt.event.*;
import java.awt.font.*;
import java.awt.geom.*;
import java.io.*;
import java.util.*;
import javax.swing.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.geom.*;
import org.jhotdraw.samples.svg.*;
import org.jhotdraw.samples.svg.SVGConstants;
import org.jhotdraw.util.*;
import org.jhotdraw.xml.*;
import static org.jhotdraw.samples.svg.SVGAttributeKeys.*;
/**
 * SVGText.
 * <p>
 * XXX - At least on Mac OS X - Always draw text using TextLayout.getOutline(),
 * because outline layout does not match with TextLayout.draw() output.
 * Cache outline to improve performance.
 *
 * @author Werner Randelshofer
 * @version $Id: SVGTextFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 * <br>2.1 2007-05-13 Fixed transformation issues.
 * <br>2.0 2007-04-14 Adapted for new AttributeKeys.TRANSFORM support.
 * <br>1.0 July 8, 2006 Created.
 */
public class SVGTextFigure
        extends SVGAttributedFigure
        implements TextHolderFigure, SVGFigure {
    
    protected Point2D.Double[] coordinates = new Point2D.Double[] { new Point2D.Double() };
    protected double[] rotates = new double[] { 0 };
    private boolean editable = true;
    
    /**
     * This is used to perform faster drawing and hit testing.
     */
    private transient Shape cachedTextShape;
    private transient Rectangle2D.Double cachedBounds;
    private transient Rectangle2D.Double cachedDrawingArea;
    
    /** Creates a new instance. */
    public SVGTextFigure() {
        this("Text");
    }
    public SVGTextFigure(String text) {
        setText(text);
        SVGAttributeKeys.setDefaults(this);
    }

    // DRAWING
    protected void drawText(java.awt.Graphics2D g) {
    }
    protected void drawFill(Graphics2D g) {
        g.fill(getTextShape());
    }
    
    protected void drawStroke(Graphics2D g) {
        g.draw(getTextShape());
    }
    
    // SHAPE AND BOUNDS
    public void setCoordinates(Point2D.Double[] coordinates) {
        this.coordinates = coordinates;
        invalidate();
    }
    
    public Point2D.Double[] getCoordinates() {
        Point2D.Double[] c = new Point2D.Double[coordinates.length];
        for (int i=0; i < c.length; i++) {
            c[i] = (Point2D.Double) coordinates[i].clone();
        }
        return c;
    }
    
    public void setRotates(double[] rotates) {
        this.rotates = rotates;
        invalidate();
    }
    public double[] getRotates() {
        return (double[]) rotates.clone();
    }
    
    public Rectangle2D.Double getBounds() {
        if (cachedBounds == null) {
            cachedBounds = new Rectangle2D.Double();
            cachedBounds.setRect(getTextShape().getBounds2D());

            String text = getText();
            if (text == null || text.length() == 0) {
                text = " ";
            }

            FontRenderContext frc = getFontRenderContext();
            HashMap<TextAttribute,Object> textAttributes = new HashMap<TextAttribute,Object>();
            textAttributes.put(TextAttribute.FONT, getFont());
            if (FONT_UNDERLINE.get(this)) {
                textAttributes.put(TextAttribute.UNDERLINE, TextAttribute.UNDERLINE_ON);
            }
            TextLayout textLayout = new TextLayout(text, textAttributes, frc);

           cachedBounds.setRect(coordinates[0].x,coordinates[0].y-textLayout.getAscent(), textLayout.getAdvance(), textLayout.getAscent());
            
            AffineTransform tx = new AffineTransform();
            tx.translate(coordinates[0].x, coordinates[0].y);
            switch (TEXT_ANCHOR.get(this)) {
                case END :
                    cachedBounds.x -=textLayout.getAdvance();
                    break;
                case MIDDLE :
                    cachedBounds.x -=textLayout.getAdvance() / 2d;
                    break;
                case START :
                    break;
            }
            tx.rotate(rotates[0]);

        }
        return (Rectangle2D.Double) cachedBounds.clone();
    }
    @Override public Rectangle2D.Double getDrawingArea() {
        if (cachedDrawingArea == null) {
            Rectangle2D rx = getTextShape().getBounds2D();
            Rectangle2D.Double r = (rx instanceof Rectangle2D.Double) ?
                (Rectangle2D.Double) rx :
                new Rectangle2D.Double(rx.getX(), rx.getY(), rx.getWidth(), rx.getHeight());
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
        return getTextShape().getBounds2D().contains(p);
    }
    
    private Shape getTextShape() {
        if (cachedTextShape == null) {
            String text = getText();
            if (text == null || text.length() == 0) {
                text = " ";
            }
            
            FontRenderContext frc = getFontRenderContext();
            HashMap<TextAttribute,Object> textAttributes = new HashMap<TextAttribute,Object>();
            textAttributes.put(TextAttribute.FONT, getFont());
            if (FONT_UNDERLINE.get(this)) {
                textAttributes.put(TextAttribute.UNDERLINE, TextAttribute.UNDERLINE_ON);
            }
            TextLayout textLayout = new TextLayout(text, textAttributes, frc);
            
            AffineTransform tx = new AffineTransform();
            tx.translate(coordinates[0].x, coordinates[0].y);
            switch (TEXT_ANCHOR.get(this)) {
                case END :
                    tx.translate(-textLayout.getAdvance(), 0);
                    break;
                case MIDDLE :
                    tx.translate(-textLayout.getAdvance() / 2d, 0);
                    break;
                case START :
                    break;
            }
            tx.rotate(rotates[0]);
            
            /*
            if (TRANSFORM.get(this) != null) {
                tx.preConcatenate(TRANSFORM.get(this));
            }*/
            
            cachedTextShape = tx.createTransformedShape(textLayout.getOutline(tx));
            cachedTextShape = textLayout.getOutline(tx);
        }
        return cachedTextShape;
    }

    
    public void setBounds(Point2D.Double anchor, Point2D.Double lead) {
        coordinates = new Point2D.Double[] {
            new Point2D.Double(anchor.x, anchor.y)
        };
        rotates = new double[] { 0d };
    }
    /**
     * Transforms the figure.
     *
     * @param tx the transformation.
     */
    public void transform(AffineTransform tx) {
        if (TRANSFORM.get(this) != null ||
                tx.getType() != (tx.getType() & AffineTransform.TYPE_TRANSLATION)) {
            if (TRANSFORM.get(this) == null) {
                TRANSFORM.basicSet(this, (AffineTransform) tx.clone());
            } else {
                AffineTransform t = TRANSFORM.getClone(this);
                t.preConcatenate(tx);
                TRANSFORM.basicSet(this, t);
            }
        } else {
            for (int i=0; i < coordinates.length; i++) {
                tx.transform(coordinates[i], coordinates[i]);
            }
            if (FILL_GRADIENT.get(this) != null &&
                    ! FILL_GRADIENT.get(this).isRelativeToFigureBounds()) {
                Gradient g = FILL_GRADIENT.getClone(this);
                g.transform(tx);
                FILL_GRADIENT.basicSet(this, g);
            }
            if (STROKE_GRADIENT.get(this) != null && 
                    ! STROKE_GRADIENT.get(this).isRelativeToFigureBounds()) {
                Gradient g = STROKE_GRADIENT.getClone(this);
                g.transform(tx);
                STROKE_GRADIENT.basicSet(this, g);
            }
        }
        invalidate();
    }
    public void restoreTransformTo(Object geometry) {
        Object[] restoreData = (Object[]) geometry;
        TRANSFORM.basicSetClone(this, (AffineTransform) restoreData[0]);
        Point2D.Double[] restoredCoordinates = (Point2D.Double[]) restoreData[1];
        for (int i=0; i < this.coordinates.length; i++) {
            coordinates[i] = (Point2D.Double) restoredCoordinates[i].clone();
        }
        FILL_GRADIENT.basicSetClone(this, (Gradient) restoreData[2]);
        STROKE_GRADIENT.basicSetClone(this, (Gradient) restoreData[3]);
        invalidate();
    }
    
    public Object getTransformRestoreData() {
        Point2D.Double[] restoredCoordinates = (Point2D.Double[]) this.coordinates.clone();
        for (int i=0; i < this.coordinates.length; i++) {
            restoredCoordinates[i] = (Point2D.Double) this.coordinates[i].clone();
        }
        return new Object[] {
            TRANSFORM.getClone(this),
            restoredCoordinates,
            FILL_GRADIENT.getClone(this),
            STROKE_GRADIENT.getClone(this),
        };
    }
    
    // ATTRIBUTES
    /**
     * Gets the text shown by the text figure.
     */
    public String getText() {
        return (String) getAttribute(TEXT);
    }
    @Override
    public <T> void setAttribute(AttributeKey<T> key, T newValue) {
        if (key .equals( SVGAttributeKeys.TRANSFORM )||
                key .equals( SVGAttributeKeys.FONT_FACE) ||
                key .equals( SVGAttributeKeys.FONT_BOLD) ||
                key .equals(SVGAttributeKeys.FONT_ITALIC) ||
                key .equals(SVGAttributeKeys.FONT_SIZE)) {
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
    public boolean isEditable() {
        return editable;
    }
    public void setEditable(boolean b) {
        this.editable = b;
    }
    
    public int getTextColumns() {
        //return (getText() == null) ? 4 : Math.min(getText().length(), 4);
        return 4;
    }
    
    public Font getFont() {
        return SVGAttributeKeys.getFont(this);
    }
    
    public Color getTextColor() {
        return FILL_COLOR.get(this);
        //   return TEXT_COLOR.get(this);
    }
    
    public Color getFillColor() {
        return FILL_COLOR.get(this) == null || FILL_COLOR.get(this).equals(Color.white) ? Color.black : Color.WHITE;
        //  return FILL_COLOR.get(this);
    }
    
    public void setFontSize(float size) {
        // FONT_SIZE.basicSet(this, new Double(size));
        Point2D.Double p = new Point2D.Double(0, size);
        AffineTransform tx =  TRANSFORM.get(this);
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
        //   return FONT_SIZE.get(this).floatValue();
        Point2D.Double p = new Point2D.Double(0, FONT_SIZE.get(this));
        AffineTransform tx =  TRANSFORM.get(this);
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
    // CONNECTING
    
    
    @Override public void invalidate() {
        super.invalidate();
        cachedTextShape = null;
        cachedBounds = null;
        cachedDrawingArea = null;
    }
    public Dimension2DDouble getPreferredSize() {
        Rectangle2D.Double b = getBounds();
        return new Dimension2DDouble(b.width, b.height);
    }
    
    public Collection<Handle> createHandles(int detailLevel) {
        LinkedList<Handle> handles = new LinkedList<Handle>();
        switch (detailLevel % 2) {
            case -1 : // Mouse hover handles
                handles.add(new BoundsOutlineHandle(this, false, true));
                break;
            case 0 :
                handles.add(new BoundsOutlineHandle(this));
                handles.add(new MoveHandle(this, RelativeLocator.northWest()));
                handles.add(new MoveHandle(this, RelativeLocator.northEast()));
                handles.add(new MoveHandle(this, RelativeLocator.southWest()));
                handles.add(new MoveHandle(this, RelativeLocator.southEast()));
                handles.add(new FontSizeHandle(this));
                handles.add(new LinkHandle(this));
                break;
            case 1 :
                TransformHandleKit.addTransformHandles(this, handles);
                break;
        }
        return handles;
    }
    // CONNECTING
    @Override
    public boolean canConnect() {
        return false; // SVG does not support connecting
    }
    @Override
    public Connector findConnector(Point2D.Double p, ConnectionFigure prototype) {
        return null; // SVG does not support connectors
    }
    @Override
    public Connector findCompatibleConnector(Connector c, boolean isStartConnector) {
        return null; // SVG does not support connectors
    }
    
    /**
     * Returns a specialized tool for the given coordinate.
     * <p>Returns null, if no specialized tool is available.
     */
    @Override
    public Tool getTool(Point2D.Double p) {
        if (isEditable() && contains(p)) {
            TextEditingTool tool = new TextEditingTool(this);
            return tool;
        }
        return null;
    }
    
    public double getBaseline() {
        return coordinates[0].y - getBounds().y;
    }
    
    /**
     * Gets the number of characters used to expand tabs.
     */
    public int getTabSize() {
        return 8;
    }
    
    public TextHolderFigure getLabelFor() {
        return this;
    }
    
    public Insets2D.Double getInsets() {
        return new Insets2D.Double();
    }
    
    public SVGTextFigure clone() {
        SVGTextFigure that = (SVGTextFigure) super.clone();
        that.coordinates = new Point2D.Double[this.coordinates.length];
        for (int i=0; i < this.coordinates.length; i++) {
            that.coordinates[i] = (Point2D.Double) this.coordinates[i].clone();
        }
        that.rotates = (double[]) this.rotates.clone();
        that.cachedBounds = null;
        that.cachedDrawingArea = null;
        that.cachedTextShape = null;
        return that;
    }
    
    public boolean isEmpty() {
        return getText() == null || getText().length() == 0;
    }

    public boolean isTextOverflow() {
        return false;
    }
}

/*
 * @(#)ODGPathFigure.java
 *
 * Copyright (c) 2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.samples.odg.figures;

import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.util.*;
import javax.swing.*;
import javax.swing.undo.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.draw.action.*;
import org.jhotdraw.geom.*;
import org.jhotdraw.samples.odg.*;
import org.jhotdraw.samples.odg.ODGConstants;
import org.jhotdraw.undo.*;
import org.jhotdraw.util.*;
import org.jhotdraw.xml.*;
import static org.jhotdraw.samples.odg.ODGAttributeKeys.*;

/**
 * ODGPath is a composite Figure which contains one or more
 * ODGBezierFigures as its children.
 *
 * @author Werner Randelshofer
 * @version $Id: ODGPathFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class ODGPathFigure extends AbstractAttributedCompositeFigure implements ODGFigure {
    /**
     * This cachedPath is used for drawing.
     */
    private transient GeneralPath cachedPath;
    //private transient Rectangle2D.Double cachedDrawingArea;
    
    private final static boolean DEBUG = false;
    
    /** Creates a new instance. */
    public ODGPathFigure() {
        add(new ODGBezierFigure());
        ODGAttributeKeys.setDefaults(this);
    }
    
    
    public void draw(Graphics2D g)  {
        double opacity = OPACITY.get(this);
        opacity = Math.min(Math.max(0d, opacity), 1d);
        if (opacity != 0d) {
            if (opacity != 1d) {
                Rectangle2D.Double drawingArea = getDrawingArea();
                
                Rectangle2D clipBounds = g.getClipBounds();
                if (clipBounds != null) {
                    Rectangle2D.intersect(drawingArea, clipBounds, drawingArea);
                }
                
                if (! drawingArea.isEmpty()) {
                    
                    BufferedImage buf = new BufferedImage(
                            Math.max(1, (int) ((2 + drawingArea.width) * g.getTransform().getScaleX())),
                            Math.max(1, (int) ((2 + drawingArea.height) * g.getTransform().getScaleY())),
                            BufferedImage.TYPE_INT_ARGB);
                    Graphics2D gr = buf.createGraphics();
                    gr.scale(g.getTransform().getScaleX(), g.getTransform().getScaleY());
                    gr.translate((int) -drawingArea.x, (int) -drawingArea.y);
                    gr.setRenderingHints(g.getRenderingHints());
                    drawFigure(gr);
                    gr.dispose();
                    Composite savedComposite = g.getComposite();
                    g.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, (float) opacity));
                    g.drawImage(buf, (int) drawingArea.x, (int) drawingArea.y,
                            2 + (int) drawingArea.width, 2 + (int) drawingArea.height, null);
                    g.setComposite(savedComposite);
                }
            } else {
                drawFigure(g);
            }
        }
    }
    
    public void drawFigure(Graphics2D g) {
        AffineTransform savedTransform = null;
        if (TRANSFORM.get(this) != null) {
            savedTransform = g.getTransform();
            g.transform(TRANSFORM.get(this));
        }
        if (FILL_STYLE.get(this) != ODGConstants.FillStyle.NONE) {
            Paint paint = ODGAttributeKeys.getFillPaint(this);
            if (paint != null) {
                g.setPaint(paint);
                drawFill(g);
            }
        }
        
        if (STROKE_STYLE.get(this) != ODGConstants.StrokeStyle.NONE) {
            Paint paint = ODGAttributeKeys.getStrokePaint(this);
            if (paint != null) {
                g.setPaint(paint);
                g.setStroke(ODGAttributeKeys.getStroke(this));
                drawStroke(g);
            }
        }
        if (TRANSFORM.get(this) != null) {
            g.setTransform(savedTransform);
        }
    }
    
    public void drawFill(Graphics2D g) {
        boolean isClosed = CLOSED.get(getChild(0));
        if (isClosed) {
            g.fill(getPath());
        }
    }
    public void drawStroke(Graphics2D g) {
        g.draw(getPath());
    }
    
    public void invalidate() {
        super.invalidate();
        cachedPath = null;
        cachedDrawingArea = null;
    }
    
    protected GeneralPath getPath() {
        if (cachedPath == null) {
            cachedPath = new GeneralPath();
            cachedPath.setWindingRule(WINDING_RULE.get(this) == WindingRule.EVEN_ODD ?
                GeneralPath.WIND_EVEN_ODD :
                GeneralPath.WIND_NON_ZERO
                    );
            for (Figure child : getChildren()) {
                ODGBezierFigure b = (ODGBezierFigure) child;
                cachedPath.append(b.getBezierPath(), false);
            }
        }
        return cachedPath;
    }
    
    public Rectangle2D.Double getDrawingArea() {
        if (cachedDrawingArea == null) {
            double strokeTotalWidth = AttributeKeys.getStrokeTotalWidth(this);
            double width = strokeTotalWidth / 2d;
            if (STROKE_JOIN.get(this) == BasicStroke.JOIN_MITER) {
                width *= STROKE_MITER_LIMIT.get(this);
            } else if (STROKE_CAP.get(this) != BasicStroke.CAP_BUTT) {
                width += strokeTotalWidth * 2;
            }
            GeneralPath gp = (GeneralPath) getPath();
            Rectangle2D strokeRect = new Rectangle2D.Double(0,0,width,width);
            if (TRANSFORM.get(this) != null) {
                gp = (GeneralPath) gp.clone();
                gp.transform(TRANSFORM.get(this));
                strokeRect = TRANSFORM.get(this).createTransformedShape(strokeRect).getBounds2D();
            }
            Rectangle2D rx = gp.getBounds2D();
            Rectangle2D.Double r = (rx instanceof Rectangle2D.Double) ?
                (Rectangle2D.Double) rx :
                new Rectangle2D.Double(rx.getX(), rx.getY(), rx.getWidth(), rx.getHeight());
            Geom.grow(r, strokeRect.getWidth(), strokeRect.getHeight());
            cachedDrawingArea = r;
        }
        return (Rectangle2D.Double) cachedDrawingArea.clone();
    }
    
    @Override final public void write(DOMOutput out) throws IOException {
        throw new UnsupportedOperationException("Use ODGStorableOutput to write this Figure.");
    }
    @Override final public void read(DOMInput in) throws IOException {
        throw new UnsupportedOperationException("Use ODGStorableInput to read this Figure.");
    }
    
    public boolean contains(Point2D.Double p) {
        getPath();
        if (TRANSFORM.get(this) != null) {
            try {
                p = (Point2D.Double) TRANSFORM.get(this).inverseTransform(p, new Point2D.Double());
            } catch (NoninvertibleTransformException ex) {
                ex.printStackTrace();
            }
        }
        /*
        return cachedPath.contains(p2);
         */
        boolean isClosed = CLOSED.get(getChild(0));
        double tolerance = Math.max(2f, AttributeKeys.getStrokeTotalWidth(this) / 2d);
        if (isClosed) {
            if (getPath().contains(p)) {
                return true;
            }
            double grow = AttributeKeys.getPerpendicularHitGrowth(this) * 2d;
            GrowStroke gs = new GrowStroke((float) grow,
                    (float) (AttributeKeys.getStrokeTotalWidth(this) *
                    STROKE_MITER_LIMIT.get(this))
                    );
            if (gs.createStrokedShape(getPath()).contains(p)) {
                return true;
            } else {
                if (isClosed) {
                    return false;
                }
            }
        }
        if (! isClosed) {
            if (Shapes.outlineContains(getPath(), p, tolerance)) {
                return true;
            }
        }
        return false;
    }
    public void setBounds(Point2D.Double anchor, Point2D.Double lead) {
        if (getChildCount() == 1 && ((ODGBezierFigure) getChild(0)).getNodeCount() <= 2) {
            ODGBezierFigure b = (ODGBezierFigure) getChild(0);
            b.setBounds(anchor, lead);
            invalidate();
        } else {
            super.setBounds(anchor, lead);
        }
    }
    public void transform(AffineTransform tx) {
        if (TRANSFORM.get(this) != null ||
                (tx.getType() & (AffineTransform.TYPE_TRANSLATION)) != tx.getType()) {
            if (TRANSFORM.get(this) == null) {
                TRANSFORM.basicSetClone(this, tx);
            } else {
                AffineTransform t = TRANSFORM.getClone(this);
                t.preConcatenate(tx);
                TRANSFORM.basicSet(this, t);
            }
        } else {
            for (Figure f : getChildren()) {
                f.transform(tx);
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
    @Override
    @SuppressWarnings("unchecked")
    public void restoreTransformTo(Object geometry) {
        invalidate();
        Object[] restoreData = (Object[]) geometry;
        ArrayList<BezierPath> paths = (ArrayList<BezierPath>) restoreData[0];
        for (int i=0, n = getChildCount(); i < n; i++) {
            getChild(i).setBezierPath(paths.get(i));
        }
        TRANSFORM.basicSetClone(this, (AffineTransform) restoreData[1]);
        FILL_GRADIENT.basicSetClone(this, (Gradient) restoreData[2]);
        STROKE_GRADIENT.basicSetClone(this, (Gradient) restoreData[3]);
    }
    
    @Override
    @SuppressWarnings("unchecked")
    public Object getTransformRestoreData() {
        ArrayList<BezierPath> paths = new ArrayList<BezierPath>(getChildCount());
        for (int i=0, n = getChildCount(); i < n; i++) {
            paths.add(getChild(i).getBezierPath());
        }
        return new Object[] {
            paths,
            TRANSFORM.getClone(this),
            FILL_GRADIENT.getClone(this),
            STROKE_GRADIENT.getClone(this),
        };
    }
    @Override
    public <T> void setAttribute(AttributeKey<T> key, T newValue) {
        super.setAttribute(key, newValue);
        invalidate();
    }
    @Override
    protected <T> void setAttributeOnChildren(AttributeKey<T> key, T newValue) {
        // empty!
    }
    
    public boolean isEmpty() {
        for (Figure child : getChildren()) {
            ODGBezierFigure b = (ODGBezierFigure) child;
            if (b.getNodeCount() > 0) {
                return false;
            }
        }
        return true;
    }
    
    @Override public Collection<Handle> createHandles(int detailLevel) {
        LinkedList<Handle> handles = new LinkedList<Handle>();
        switch (detailLevel % 2) {
            case 0 :
                handles.add(new ODGPathOutlineHandle(this));
                for (Figure child : getChildren()) {
                    handles.addAll(((ODGBezierFigure) child).createHandles(this, detailLevel));
                }
                break;
            case 1 :
                TransformHandleKit.addTransformHandles(this, handles);
                break;
            default:
                break;
        }
        return handles;
    }
    
    @Override public Collection<Action> getActions(Point2D.Double p) {
        final ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.odg.Labels");
        LinkedList<Action> actions = new LinkedList<Action>();
        if (TRANSFORM.get(this) != null) {
            actions.add(new AbstractAction(labels.getString("edit.removeTransform.text")) {
                public void actionPerformed(ActionEvent evt) {
                    ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.samples.odg.Labels");
                    ODGPathFigure.this.willChange();
                    fireUndoableEditHappened(
                            TRANSFORM.setUndoable(ODGPathFigure.this, null)
                            );
                    ODGPathFigure.this.changed();
                }
            });
            actions.add(new AbstractAction(labels.getString("edit.flattenTransform.text")) {
                public void actionPerformed(ActionEvent evt) {
                    // CompositeEdit edit = new CompositeEdit(labels.getString("flattenTransform"));
                    //TransformEdit edit = new TransformEdit(ODGPathFigure.this, )
                    final Object restoreData = getTransformRestoreData();
                    UndoableEdit edit = new AbstractUndoableEdit() {
                        public String getPresentationName() {
                            return labels.getString("flattenTransform");
                        }
                        
                        public void undo() throws CannotUndoException {
                            super.undo();
                            willChange();
                            restoreTransformTo(restoreData);
                            changed();
                        }
                        
                        public void redo() throws CannotRedoException {
                            super.redo();
                            willChange();
                            restoreTransformTo(restoreData);
                            flattenTransform();
                            changed();
                        }
                    };
                    willChange();
                    flattenTransform();
                    changed();
                    fireUndoableEditHappened(edit);
                }
            });
        }
        actions.add(new AbstractAction(labels.getString("closePath")) {
            public void actionPerformed(ActionEvent evt) {
                for (Figure child : getChildren()) {
                    ODGPathFigure.this.willChange();
                    getDrawing().fireUndoableEditHappened(
                            CLOSED.setUndoable(child, true)
                            );
                    ODGPathFigure.this.changed();
                }
            }
        });
        actions.add(new AbstractAction(labels.getString("openPath")) {
            public void actionPerformed(ActionEvent evt) {
                for (Figure child : getChildren()) {
                    ODGPathFigure.this.willChange();
                    getDrawing().fireUndoableEditHappened(
                            CLOSED.setUndoable(child, false)
                            );
                    ODGPathFigure.this.changed();
                }
            }
        });
        actions.add(new AbstractAction(labels.getString("windingRule.evenOdd")) {
            public void actionPerformed(ActionEvent evt) {
                ODGPathFigure.this.willChange();
                getDrawing().fireUndoableEditHappened(
                        WINDING_RULE.setUndoable(ODGPathFigure.this, WindingRule.EVEN_ODD)
                        );
                ODGPathFigure.this.changed();
            }
        });
        actions.add(new AbstractAction(labels.getString("windingRule.nonZero")) {
            public void actionPerformed(ActionEvent evt) {
                WINDING_RULE.set(ODGPathFigure.this, WindingRule.NON_ZERO);
                getDrawing().fireUndoableEditHappened(
                        WINDING_RULE.setUndoable(ODGPathFigure.this, WindingRule.EVEN_ODD)
                        );
            }
        });
        return actions;
    }
    // CONNECTING
    public boolean canConnect() {
        return false; // ODG does not support connecting
    }
    public Connector findConnector(Point2D.Double p, ConnectionFigure prototype) {
        return null; // ODG does not support connectors
    }
    public Connector findCompatibleConnector(Connector c, boolean isStartConnector) {
        return null; // ODG does not support connectors
    }
    /**
     * Handles a mouse click.
     */
    @Override public boolean handleMouseClick(Point2D.Double p, MouseEvent evt, DrawingView view) {
        if (evt.getClickCount() == 2 && view.getHandleDetailLevel() % 2 == 0) {
            for (Figure child : getChildren()) {
                ODGBezierFigure bf = (ODGBezierFigure) child;
                int index = bf.getBezierPath().findSegment(p, (float) (5f / view.getScaleFactor()));
                if (index != -1) {
                    bf.handleMouseClick(p, evt, view);
                    evt.consume();
                    return true;
                }
            }
        }
        return false;
    }
    
    @Override public void add(final int index, final Figure figure) {
        super.add(index, (ODGBezierFigure) figure);
    }
    
    @Override public ODGBezierFigure getChild(int index) {
        return (ODGBezierFigure) super.getChild(index);
    }
    public ODGPathFigure clone() {
        ODGPathFigure that = (ODGPathFigure) super.clone();
        return that;
    }
    
    public void flattenTransform() {
        willChange();
        AffineTransform tx = TRANSFORM.get(this);
        if (tx != null) {
            for (Figure child : getChildren()) {
                ((ODGBezierFigure) child).transform(tx);
                ((ODGBezierFigure) child).flattenTransform();
            }
        }
        TRANSFORM.basicSet(this, null);
        changed();
    }
}

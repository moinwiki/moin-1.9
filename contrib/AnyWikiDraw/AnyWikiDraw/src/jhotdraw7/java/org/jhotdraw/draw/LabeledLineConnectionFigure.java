/*
 * @(#)LabeledLineConnection.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.draw;

import org.jhotdraw.util.*;
import java.util.*;
import java.awt.*;
import java.awt.geom.*;
import javax.swing.event.*;

/**
 * A LineConnection with labels.
 * <p>
 * Usage:
 * <pre>
 * LineConnectionFigure lcf = new LineConnectionFigure();
 * lcf.setLayouter(new LocatorLayouter());
 * TextFigure label = new TextFigure();
 * label.setText("Hello");
 * LocatorLayouter.LAYOUT_LOCATOR.set(label, new BezierLabelLocator(0, -Math.PI / 4, 8));
 * lcf.add(label);
 * </pre>
 *
 * @author Werner Randelshofer
 * @version $Id: LabeledLineConnectionFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class LabeledLineConnectionFigure extends LineConnectionFigure
        implements CompositeFigure {
    
    private Layouter layouter;
    private ArrayList<Figure> children = new ArrayList<Figure>();
    private transient Rectangle2D.Double cachedDrawingArea;
    
    /**
     * Handles figure changes in the children.
     */
    private ChildHandler childHandler = new ChildHandler(this);
    private static class ChildHandler extends FigureAdapter implements UndoableEditListener {
        private LabeledLineConnectionFigure owner;
        private ChildHandler(LabeledLineConnectionFigure owner) {
            this.owner = owner;
        }
        @Override public void figureRequestRemove(FigureEvent e) {
            owner.remove(e.getFigure());
        }
        
        @Override public void figureChanged(FigureEvent e) {
            if (! owner.isChanging()) {
                owner.willChange();
                owner.fireFigureChanged(e);
                owner.changed();
            }
        }
        
        @Override public void areaInvalidated(FigureEvent e) {
            if (! owner.isChanging()) {
                owner.fireAreaInvalidated(e.getInvalidatedArea());
            }
        }

        public void undoableEditHappened(UndoableEditEvent e) {
            owner.fireUndoableEditHappened(e.getEdit());
        }
    };
    /** Creates a new instance. */
    public LabeledLineConnectionFigure() {
    }
    // DRAWING
    /**
     * Draw the figure. This method is delegated to the encapsulated presentation figure.
     */
    public void draw(Graphics2D g) {
        super.draw(g);
        for (Figure child : children) {
            if (child.isVisible()) {
                child.draw(g);
            }
        }
    }
    
    // SHAPE AND BOUNDS
    /**
     * Transforms the figure.
     */
    public void transform(AffineTransform tx) {
        super.transform(tx);
        for (Figure f : children) {
            f.transform(tx);
        }
        invalidate();
    }
    public Rectangle2D.Double getDrawingArea() {
        if (cachedDrawingArea == null) {
            cachedDrawingArea = super.getDrawingArea();
            for (Figure child : getChildrenFrontToBack()) {
                if (child.isVisible()) {
                    Rectangle2D.Double childBounds = child.getDrawingArea();
                    if (! childBounds.isEmpty()) {
                        cachedDrawingArea.add(childBounds);
                    }
                }
            }
        }
        return (Rectangle2D.Double) cachedDrawingArea.clone();
    }
    public boolean contains(Point2D.Double p) {
        if (getDrawingArea().contains(p)) {
            for (Figure child : getChildrenFrontToBack()) {
                if (child.isVisible() && child.contains(p)) return true;
            }
            return super.contains(p);
        }
        return false;
    }
    // ATTRIBUTES
    /**
     * Sets an attribute of the figure.
     * AttributeKey name and semantics are defined by the class implementing
     * the figure interface.
     */
    public <T> void setAttribute(AttributeKey<T> key, T newValue) {
        super.setAttribute(key, newValue);
        if (isAttributeEnabled(key)) {
            if (children != null) {
                for (Figure child : children) {
                    key.basicSet(child, newValue);
                }
            }
        }
    }
    // EDITING
    public Figure findFigureInside(Point2D.Double p) {
        if (getDrawingArea().contains(p)) {
            Figure found = null;
            for (Figure child : getChildrenFrontToBack()) {
                if (child.isVisible()) {
                    found = child.findFigureInside(p);
                    if (found != null) {
                        return found;
                    }
                }
            }
        }
        return null;
    }
    // CONNECTING
    public void updateConnection() {
        super.updateConnection();
        layout();
    }
    
    // COMPOSITE FIGURES
    public java.util.List<Figure> getChildren() {
        return Collections.unmodifiableList(children);
    }
    public int getChildCount() {
        return children.size();
    }
    public Figure getChild(int index) {
        return children.get(index);
    }
    /**
     * Returns an iterator to iterate in
     * Z-order front to back over the children.
     */
    public java.util.List<Figure> getChildrenFrontToBack() {
        return children ==  null ?
            new LinkedList<Figure>() :
            new ReversedList<Figure>(children);
    }
    
    public boolean add(Figure figure) {
        basicAdd(figure);
        if (getDrawing() != null) {
            figure.addNotify(getDrawing());
        }
        return true;
    }
    public void add(int index, Figure figure) {
        basicAdd(index, figure);
        if (getDrawing() != null) {
            figure.addNotify(getDrawing());
        }
    }
    public void basicAdd(Figure figure) {
        basicAdd(children.size(), figure);
    }
    public void basicAdd(int index, Figure figure) {
        children.add(index, figure);
        figure.addFigureListener(childHandler);
        invalidate();
    }
    public boolean remove(final Figure figure) {
        int index = children.indexOf(figure);
        if (index == -1) {
            return false;
        } else {
            willChange();
            basicRemoveChild(index);
            if (getDrawing() != null) {
                figure.removeNotify(getDrawing());
            }
            changed();
            return true;
        }
    }
    public Figure removeChild(int index) {
        willChange();
        Figure figure = basicRemoveChild(index);
        if (getDrawing() != null) {
            figure.removeNotify(getDrawing());
        }
        changed();
        return figure;
    }
    public int basicRemove(final Figure figure) {
        int index = children.indexOf(figure);
        if (index != -1) {
            basicRemoveChild(index);
        }
        return index;
    }
    public Figure basicRemoveChild(int index) {
        Figure figure = children.remove(index);
        figure.removeFigureListener(childHandler);
        return figure;
    }
    
    public void removeAllChildren() {
        willChange();
        while (children.size() > 0) {
            Figure figure = basicRemoveChild(children.size() - 1);
            if (getDrawing() != null) {
                figure.removeNotify(getDrawing());
            }
        }
        changed();
    }
    public void basicRemoveAllChildren() {
        while (children.size() > 0) {
            basicRemoveChild(children.size() - 1);
        }
    }
    // LAYOUT
    /**
     * Get a Layouter object which encapsulated a layout
     * algorithm for this figure. Typically, a Layouter
     * accesses the child components of this figure and arranges
     * their graphical presentation.
     *
     *
     * @return layout strategy used by this figure
     */
    public Layouter getLayouter() {
        return layouter;
    }
    public void setLayouter(Layouter newLayouter) {
        this.layouter = newLayouter;
    }
    
    /**
     * A layout algorithm is used to define how the child components
     * should be laid out in relation to each other. The task for
     * layouting the child components for presentation is delegated
     * to a Layouter which can be plugged in at runtime.
     */
    public void layout() {
        if (getLayouter() != null) {
            Rectangle2D.Double bounds = getBounds();
            Point2D.Double p = new Point2D.Double(bounds.x, bounds.y);
            Rectangle2D.Double r = getLayouter().layout(
                    this, p, p
                    );
            invalidate();
        }
    }
    
// EVENT HANDLING
    
    public void invalidate() {
        super.invalidate();
        cachedDrawingArea = null;
    }
    public void validate() {
        super.validate();
        layout();
    }
    public void addNotify(Drawing drawing) {
        for (Figure child : new LinkedList<Figure>(children)) {
            child.addNotify(drawing);
        }
        super.addNotify(drawing);
    }
    public void removeNotify(Drawing drawing) {
        for (Figure child : new LinkedList<Figure>(children)) {
            child.removeNotify(drawing);
        }
        super.removeNotify(drawing);
    }
    public void removeCompositeFigureListener(CompositeFigureListener listener) {
        listenerList.remove(CompositeFigureListener.class, listener);
    }

    public void addCompositeFigureListener(CompositeFigureListener listener) {
        listenerList.add(CompositeFigureListener.class, listener);
    }
    /**
     *  Notify all listenerList that have registered interest for
     * notification on this event type.
     */
    protected void fireFigureAdded(Figure f, int zIndex) {
        CompositeFigureEvent event = null;
        // Notify all listeners that have registered interest for
        // Guaranteed to return a non-null array
        Object[] listeners = listenerList.getListenerList();
        // Process the listeners last to first, notifying
        // those that are interested in this event
        for (int i = listeners.length-2; i>=0; i-=2) {
            if (listeners[i] == CompositeFigureListener.class) {
                // Lazily create the event:
                if (event == null)
                    event = new CompositeFigureEvent(this, f, f.getDrawingArea(), zIndex);
                ((CompositeFigureListener)listeners[i+1]).figureAdded(event);
            }
        }
    }
    
    /**
     *  Notify all listenerList that have registered interest for
     * notification on this event type.
     */
    protected void fireFigureRemoved(Figure f, int zIndex) {
        CompositeFigureEvent event = null;
        // Notify all listeners that have registered interest for
        // Guaranteed to return a non-null array
        Object[] listeners = listenerList.getListenerList();
        // Process the listeners last to first, notifying
        // those that are interested in this event
        for (int i = listeners.length-2; i>=0; i-=2) {
            if (listeners[i] == CompositeFigureListener.class) {
                // Lazily create the event:
                if (event == null)
                    event = new CompositeFigureEvent(this, f, f.getDrawingArea(), zIndex);
                ((CompositeFigureListener)listeners[i+1]).figureRemoved(event);
            }
        }
    }
    
    // CLONING
    public LabeledLineConnectionFigure clone() {
        LabeledLineConnectionFigure that = (LabeledLineConnectionFigure) super.clone();
        that.childHandler = new ChildHandler(that);
        that.children = new ArrayList<Figure>();
        for (Figure thisChild : this.children) {
            Figure thatChild = (Figure) thisChild.clone();
            that.children.add(thatChild);
            thatChild.addFigureListener(that.childHandler);
        }
        return that;
    }
    public void remap(Map<Figure,Figure> oldToNew, boolean disconnectIfNotInMap) {
        super.remap(oldToNew, disconnectIfNotInMap);
        for (Figure child : children) {
            child.remap(oldToNew, disconnectIfNotInMap);
        }
    }

    public boolean contains(Figure f) {
        return children.contains(f);
    }

    public int indexOf(Figure child) {
        return children.indexOf(child);
    }
}

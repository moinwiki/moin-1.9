/*
 * @(#)AbstractCompositeFigure.java
 *
 * Copyright (c) 2007-2009 by the original authors of JHotDraw
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

import java.io.IOException;
import org.jhotdraw.util.*;
import java.awt.*;
import java.awt.geom.*;
import java.io.Serializable;
import java.util.*;
import javax.swing.event.*;
import org.jhotdraw.geom.*;
import org.jhotdraw.xml.DOMInput;
import org.jhotdraw.xml.DOMOutput;
import static org.jhotdraw.draw.AttributeKeys.*;

/**
 * This abstract class can be extended to implement a {@link CompositeFigure}.
 * AbstractCompositeFigure.
 *
 * @author Werner Randelshofer
 * @version $Id: AbstractCompositeFigure.java 542 2009-07-06 05:57:55Z rawcoder $
 */
public abstract class AbstractCompositeFigure
        extends AbstractFigure
        implements CompositeFigure {

    /**
     * A Layouter determines how the children of the CompositeFigure
     * are laid out graphically.
     */
    protected Layouter layouter;
    /**
     * The children that this figure is composed of
     *
     * @see #add
     * @see #removeChild
     */
    protected ArrayList<Figure> children = new ArrayList<Figure>();
    /**
     * Cached draw cachedBounds.
     */
    protected transient Rectangle2D.Double cachedDrawingArea;
    /**
     * Cached layout cachedBounds.
     */
    protected transient Rectangle2D.Double cachedBounds;
    /**
     * Handles figure changes in the children.
     */
    protected EventHandler eventHandler;

    protected class EventHandler extends FigureAdapter implements UndoableEditListener, Serializable {

        @Override
        public void figureRequestRemove(FigureEvent e) {
            remove(e.getFigure());
        }

        @Override
        public void figureChanged(FigureEvent e) {
            Rectangle2D.Double invalidatedArea = getDrawingArea();
            invalidatedArea.add(e.getInvalidatedArea());

            // We call invalidate/validate here, because we must layout
            // the figure again.
            invalidate();
            validate();

            // Forward the figureChanged event to listeners on AbstractCompositeFigure.
            invalidatedArea.add(getDrawingArea());
            fireFigureChanged(invalidatedArea);
        }

        @Override
        public void areaInvalidated(FigureEvent e) {
            fireAreaInvalidated(e);
        }

        public void undoableEditHappened(UndoableEditEvent e) {
            fireUndoableEditHappened(e.getEdit());
        }

        @Override
        public void attributeChanged(FigureEvent e) {
            invalidate();
        }

        @Override
        public void figureAdded(FigureEvent e) {
            invalidate();
        }

        @Override
        public void figureRemoved(FigureEvent e) {
            invalidate();
        }
    }

    public AbstractCompositeFigure() {
        eventHandler = createEventHandler();
    }

    @Override
    public Collection<Handle> createHandles(int detailLevel) {
        LinkedList<Handle> handles = new LinkedList<Handle>();
        if (detailLevel == 0) {
            handles.add(new BoundsOutlineHandle(this, true, false));
            TransformHandleKit.addScaleMoveTransformHandles(this, handles);
        }
        return handles;
    }

    protected EventHandler createEventHandler() {
        return new EventHandler();
    }

    public boolean add(Figure figure) {
        add(getChildCount(), figure);
        return true;
    }

    public void add(int index, Figure figure) {
        basicAdd(index, figure);
        if (getDrawing() != null) {
            figure.addNotify(getDrawing());
        }
        fireFigureAdded(figure, index);
        invalidate();
    }

    public void addAll(Collection<? extends Figure> figures) {
        addAll(getChildCount(), figures);
    }

    public final void addAll(int index, Collection<? extends Figure> figures) {
        for (Figure f : figures) {
            basicAdd(index++, f);
            if (getDrawing() != null) {
                f.addNotify(getDrawing());
            }
            fireFigureAdded(f, index);
        }
        invalidate();
    }

    public void basicAdd(Figure figure) {
        basicAdd(getChildCount(), figure);
    }

    public void basicAddAll(int index, Collection<? extends Figure> newFigures) {
        for (Figure f : newFigures) {
            basicAdd(index++, f);
        }
    }

    public void addNotify(Drawing drawing) {
        super.addNotify(drawing);
        for (Figure child : getChildren()) {
            child.addNotify(drawing);
        }
    }

    public void removeNotify(Drawing drawing) {
        super.removeNotify(drawing);
        // Copy children collection to avoid concurrent modification exception
        for (Figure child : new LinkedList<Figure>(getChildren())) {
            child.removeNotify(drawing);
        }
    }

    public boolean remove(final Figure figure) {
        int index = children.indexOf(figure);
        if (index == -1) {
            return false;
        } else {
            basicRemoveChild(index);
            if (getDrawing() != null) {
                figure.removeNotify(getDrawing());
            }
            fireFigureRemoved(figure, index);
            return true;
        }
    }

    public Figure removeChild(int index) {
        Figure removed = basicRemoveChild(index);
        if (getDrawing() != null) {
            removed.removeNotify(getDrawing());
        }
        return removed;
    }

    /**
     * Removes all specified children.
     *
     * @see #add
     */
    public void removeAll(Collection<? extends Figure> figures) {
        for (Figure f : figures) {
            remove(f);
        }
    }

    /**
     * Removes all children.
     *
     * @see #add
     */
    public void removeAllChildren() {
        willChange();
        for (Figure f : new LinkedList<Figure>(getChildren())) {
            if (getDrawing() != null) {
                f.removeNotify(getDrawing());
            }
            int index = basicRemove(f);
        }
        changed();
    }

    /**
     * Removes all children.
     *
     * @see #add
     */
    public void basicRemoveAllChildren() {
        for (Figure f : new LinkedList<Figure>(getChildren())) {
            basicRemove(f);
        }
    }

    /**
     * Removes all children.
     *
     * @see #add
     */
    public void basicRemoveAll(Collection<? extends Figure> figures) {
        for (Figure f : figures) {
            basicRemove(f);
        }
    }

    /**
     * Sends a figure to the back of the composite figure.
     *
     * @param figure that is part of this composite figure
     */
    public synchronized void sendToBack(Figure figure) {
        if (basicRemove(figure) != -1) {
            basicAdd(0, figure);
            fireAreaInvalidated(figure.getDrawingArea());
        }
    }

    /**
     * Brings a figure to the front of the drawing.
     *
     * @param figure that is part of the drawing
     */
    public synchronized void bringToFront(Figure figure) {
        if (basicRemove(figure) != -1) {
            basicAdd(figure);
            fireAreaInvalidated(figure.getDrawingArea());
        }
    }

    /**
     * Transforms the figure.
     */
    public void transform(AffineTransform tx) {
        for (Figure f : getChildren()) {
            f.transform(tx);
        }
        invalidate();
    //invalidate();
    }

    @Override
    public void setBounds(Point2D.Double anchor, Point2D.Double lead) {
        Rectangle2D.Double oldBounds = getBounds();
        Rectangle2D.Double newBounds = new Rectangle2D.Double(
                Math.min(anchor.x, lead.x),
                Math.min(anchor.y, lead.y),
                Math.abs(anchor.x - lead.x),
                Math.abs(anchor.y - lead.y));

        double sx = newBounds.width / oldBounds.width;
        double sy = newBounds.height / oldBounds.height;

        AffineTransform tx = new AffineTransform();
        tx.translate(-oldBounds.x, -oldBounds.y);
        if (!Double.isNaN(sx) && !Double.isNaN(sy) &&
                !Double.isInfinite(sx) && !Double.isInfinite(sy) &&
                (sx != 1d || sy != 1d) &&
                !(sx < 0.0001) && !(sy < 0.0001)) {
            transform(tx);
            tx.setToIdentity();
            tx.scale(sx, sy);
            transform(tx);
            tx.setToIdentity();
        }
        tx.translate(newBounds.x, newBounds.y);
        transform(tx);
    }

    /**
     * Returns an iterator to iterate in
     * Z-order front to back over the children.
     */
    public java.util.List<Figure> getChildrenFrontToBack() {
        return children.size() == 0 ? new LinkedList<Figure>() : new ReversedList<Figure>(getChildren());
    }

    public <T> void setAttribute(AttributeKey<T> key, T value) {
        for (Figure child : getChildren()) {
            child.setAttribute(key, value);
        }
        invalidate();
    }

    public <T> T getAttribute(AttributeKey<T> name) {
        return null;
    }

    public Map<AttributeKey, Object> getAttributes() {
        return new HashMap<AttributeKey, Object>();
    }

    public Object getAttributesRestoreData() {
        LinkedList<Object> data = new LinkedList<Object>();
        for (Figure child : getChildren()) {
            data.add(child.getAttributesRestoreData());
        }
        return data;
    }

    public void restoreAttributesTo(Object newData) {
        @SuppressWarnings("unchecked")
        Iterator<Object> data = ((LinkedList<Object>) newData).iterator();
        for (Figure child : getChildren()) {
            child.restoreAttributesTo(data.next());
        }
    }

    public boolean contains(Figure f) {
        return children.contains(f);
    }

    public boolean contains(Point2D.Double p) {
        if (TRANSFORM.get(this) != null) {
            try {
                p = (Point2D.Double) TRANSFORM.get(this).inverseTransform(p, new Point2D.Double());
            } catch (NoninvertibleTransformException ex) {
                InternalError error = new InternalError(ex.getMessage());
                error.initCause(ex);
                throw error;
            }
        }
        ;
        if (getDrawingArea().contains(p)) {
            for (Figure child : getChildrenFrontToBack()) {
                if (child.isVisible() && child.contains(p)) {
                    return true;
                }
            }
        }
        return false;
    }

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

    public Figure findChild(Point2D.Double p) {
        if (getBounds().contains(p)) {
            Figure found = null;
            for (Figure child : getChildrenFrontToBack()) {
                if (child.isVisible() && child.contains(p)) {
                    return child;
                }
            }
        }
        return null;
    }

    public int findChildIndex(Point2D.Double p) {
        Figure child = findChild(p);
        return (child == null) ? -1 : children.indexOf(child);
    }

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
                    this, p, p);
            setBounds(new Point2D.Double(r.x, r.y), new Point2D.Double(r.x + r.width, r.y + r.height));
            invalidate();
        }
    }

    /**
     * Set a Layouter object which encapsulated a layout
     * algorithm for this figure. Typically, a Layouter
     * accesses the child components of this figure and arranges
     * their graphical presentation. It is a good idea to set
     * the Layouter in the protected initialize() method
     * so it can be recreated if a GraphicalCompositeFigure is
     * read and restored from a StorableInput stream.
     *
     *
     * @param newLayouter	encapsulation of a layout algorithm.
     */
    public void setLayouter(Layouter newLayouter) {
        this.layouter = newLayouter;
    }

    @Override
    public Dimension2DDouble getPreferredSize() {
        if (this.layouter != null) {
            Rectangle2D.Double r = layouter.calculateLayout(this, getStartPoint(), getEndPoint());
            return new Dimension2DDouble(r.width, r.height);
        } else {
            return super.getPreferredSize();
        }
    }

    public void draw(Graphics2D g) {
        Rectangle2D clipBounds = g.getClipBounds();
        if (clipBounds != null) {
            for (Figure child : getChildren()) {
                if (child.isVisible() && child.getDrawingArea().intersects(clipBounds)) {
                    child.draw(g);
                }
            }
        } else {
            for (Figure child : getChildren()) {
                if (child.isVisible()) {
                    child.draw(g);
                }
            }
        }
    }

    @Override
    public Collection<Figure> getDecomposition() {
        LinkedList<Figure> list = new LinkedList<Figure>();
        list.add(this);
        list.addAll(getChildren());
        return list;
    }

    public void read(DOMInput in) throws IOException {
        in.openElement("children");
        for (int i = 0; i < in.getElementCount(); i++) {
            basicAdd((Figure) in.readObject(i));
        }
        in.closeElement();
    }

    public void write(DOMOutput out) throws IOException {
        out.openElement("children");
        for (Figure child : getChildren()) {
            out.writeObject(child);
        }
        out.closeElement();
    }

    public void restoreTransformTo(Object geometry) {
        LinkedList list = (LinkedList) geometry;
        Iterator i = list.iterator();
        for (Figure child : getChildren()) {
            child.restoreTransformTo(i.next());
        }
        invalidate();
    }

    public Object getTransformRestoreData() {
        LinkedList<Object> list = new LinkedList<Object>();
        for (Figure child : getChildren()) {
            list.add(child.getTransformRestoreData());
        }
        return list;
    }

    @Override
    protected void validate() {
        super.validate();
        layout();
    }

    public void basicAdd(int index, Figure figure) {
        children.add(index, figure);
        figure.addFigureListener(eventHandler);
    }

    public Figure basicRemoveChild(int index) {
        Figure figure = children.remove(index);
        figure.removeFigureListener(eventHandler);
        invalidate();
        return figure;
    }

    public java.util.List<Figure> getChildren() {
        return Collections.unmodifiableList(children);
    }

    public int getChildCount() {
        return children.size();
    }

    public Figure getChild(int index) {
        return children.get(index);
    }

    @Override
    public AbstractCompositeFigure clone() {
        AbstractCompositeFigure that = (AbstractCompositeFigure) super.clone();
        that.children = new ArrayList<Figure>();
        that.eventHandler = that.createEventHandler();
        for (Figure thisChild : this.children) {
            Figure thatChild = (Figure) thisChild.clone();
            that.children.add(thatChild);
            thatChild.addFigureListener(that.eventHandler);
        }
        return that;
    }

    @Override
    protected void invalidate() {
        cachedBounds = null;
        cachedDrawingArea = null;
    }

    public int basicRemove(Figure child) {
        int index = children.indexOf(child);
        if (index != -1) {
            basicRemoveChild(index);
        }
        return index;
    }

    public int indexOf(Figure child) {
        return children.indexOf(child);
    }

    public Rectangle2D.Double getDrawingArea() {
        if (cachedDrawingArea == null) {
            if (getChildCount() == 0) {
                cachedDrawingArea = new Rectangle2D.Double();
            } else {
                for (Figure f : children) {
                    if (cachedDrawingArea == null || cachedDrawingArea.isEmpty()) {
                        cachedDrawingArea = f.getDrawingArea();
                    } else {
                        cachedDrawingArea.add(f.getDrawingArea());
                    }
                }
            }
        }
        return (Rectangle2D.Double) cachedDrawingArea.clone();
    }

    public Rectangle2D.Double getBounds() {
        if (cachedBounds == null) {
            if (getChildCount() == 0) {
                cachedBounds = new Rectangle2D.Double();
            } else {
                for (Figure f : children) {
                    if (cachedBounds == null || cachedBounds.isEmpty()) {
                        cachedBounds = f.getBounds();
                    } else {
                        cachedBounds.add(f.getBounds());
                    }
                }
            }
        }
        return (Rectangle2D.Double) cachedBounds.clone();
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
        for (int i = listeners.length - 2; i >= 0; i -= 2) {
            if (listeners[i] == CompositeFigureListener.class) {
                // Lazily create the event:
                if (event == null) {
                    event = new CompositeFigureEvent(this, f, f.getDrawingArea(), zIndex);
                }
                ((CompositeFigureListener) listeners[i + 1]).figureAdded(event);
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
        for (int i = listeners.length - 2; i >= 0; i -= 2) {
            if (listeners[i] == CompositeFigureListener.class) {
                // Lazily create the event:
                if (event == null) {
                    event = new CompositeFigureEvent(this, f, f.getDrawingArea(), zIndex);
                }
                ((CompositeFigureListener) listeners[i + 1]).figureRemoved(event);
            }
        }
    }

    public void removeCompositeFigureListener(CompositeFigureListener listener) {
        listenerList.remove(CompositeFigureListener.class, listener);
    }

    public void addCompositeFigureListener(CompositeFigureListener listener) {
        listenerList.add(CompositeFigureListener.class, listener);
    }
}

/*
 * @(#)DefaultDrawingView.java
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
package org.jhotdraw.draw;

import javax.swing.event.*;
import javax.swing.undo.*;
import org.jhotdraw.util.*;
import java.awt.*;
import java.awt.geom.*;
import java.awt.event.*;
import java.awt.image.BufferedImage;
import java.util.*;
import javax.swing.*;
import org.jhotdraw.app.EditableComponent;
import static org.jhotdraw.draw.AttributeKeys.*;

/**
 * A default implementation of {@link DrawingView} suited for viewing drawings
 * with a small number of figures.
 *
 * FIXME - Implement clone Method.
 * FIXME - Use double buffering for the drawing to improve performance.
 *
 * @author Werner Randelshofer
 * @version $Id: DefaultDrawingView.java 540 2009-07-04 11:38:15Z rawcoder $
 */
public class DefaultDrawingView
        extends JComponent
        implements DrawingView, EditableComponent {

    /**
     * Set this to true to turn on debugging output on System.out.
     */
    private final static boolean DEBUG = false;
    private Drawing drawing;
    private Set<Figure> dirtyFigures = new HashSet<Figure>();
    /**
     * Holds the selected figures in an ordered set. The ordering reflects
     * the sequence that was used to select the figures.
     */
    private Set<Figure> selectedFigures = new LinkedHashSet<Figure>();
    //private int rainbow = 0;
    private LinkedList<Handle> selectionHandles = new LinkedList<Handle>();
    private boolean isConstrainerVisible = false;
    private Constrainer visibleConstrainer = new GridConstrainer(8, 8);
    private Constrainer invisibleConstrainer = new GridConstrainer();
    private Handle secondaryHandleOwner;
    private Handle activeHandle;
    private LinkedList<Handle> secondaryHandles = new LinkedList<Handle>();
    private boolean handlesAreValid = true;
    private transient Dimension cachedPreferredSize;
    private double scaleFactor = 1;
    private Point2D.Double translate = new Point2D.Double(0, 0);
    private int detailLevel;
    private DrawingEditor editor;
    private JLabel emptyDrawingLabel;
    private FigureListener handleInvalidator = new FigureAdapter() {

        @Override
        public void figureHandlesChanged(FigureEvent e) {
            invalidateHandles();
        }
    };
    private ChangeListener changeHandler = new ChangeListener() {

        public void stateChanged(ChangeEvent evt) {
            repaint();
        }
    };
    private transient Rectangle2D.Double cachedDrawingArea;

    public void repaintHandles() {
        validateHandles();
        Rectangle r = null;
        for (Handle h : getSelectionHandles()) {
            if (r == null) {
                r = h.getDrawingArea();
            } else {
                r.add(h.getDrawingArea());
            }
        }
        for (Handle h : getSecondaryHandles()) {
            if (r == null) {
                r = h.getDrawingArea();
            } else {
                r.add(h.getDrawingArea());
            }
        }
        if (r != null) {
            repaint(r);
        }
    }

    /** Draws the background of the drawing view. */
    protected void drawBackground(Graphics2D g) {
        g.setColor(getBackground());
        g.fillRect(0,0,getWidth(),getHeight());
    }

    private class EventHandler implements FigureListener, CompositeFigureListener, HandleListener, FocusListener {

        public void figureAdded(CompositeFigureEvent evt) {
            if (drawing.getChildCount() == 1 && getEmptyDrawingMessage() != null) {
                repaint();
            } else {
                repaintDrawingArea(evt.getInvalidatedArea());
            }
            invalidateDimension();
        }

        public void figureRemoved(CompositeFigureEvent evt) {
            if (drawing.getChildCount() == 0 && getEmptyDrawingMessage() != null) {
                repaint();
            } else {
                repaintDrawingArea(evt.getInvalidatedArea());
            }
            removeFromSelection(evt.getChildFigure());
            invalidateDimension();
        }

        public void areaInvalidated(FigureEvent evt) {
            repaintDrawingArea(evt.getInvalidatedArea());
            invalidateDimension();
        }

        public void areaInvalidated(HandleEvent evt) {
            repaint(evt.getInvalidatedArea());
            invalidateDimension();
        }

        public void handleRequestSecondaryHandles(HandleEvent e) {
            secondaryHandleOwner = e.getHandle();
            secondaryHandles.clear();
            secondaryHandles.addAll(secondaryHandleOwner.createSecondaryHandles());
            for (Handle h : secondaryHandles) {
                h.setView(DefaultDrawingView.this);
                h.addHandleListener(eventHandler);
            }
            repaint();
        }

        public void focusGained(FocusEvent e) {
            //   repaintHandles();
            if (editor != null) {
                editor.setActiveView(DefaultDrawingView.this);
            }
        }

        public void focusLost(FocusEvent e) {
            //   repaintHandles();
        }

        public void handleRequestRemove(HandleEvent e) {
            selectionHandles.remove(e.getHandle());
            e.getHandle().dispose();
            invalidateHandles();
            repaint(e.getInvalidatedArea());
        }

        public void attributeChanged(FigureEvent e) {
            if (e.getSource() == drawing) {
                if (e.getAttribute().equals(CANVAS_HEIGHT) || e.getAttribute().equals(CANVAS_WIDTH)) {
                    validateViewTranslation();
                }
                repaint();
            } else {
                repaintDrawingArea(e.getInvalidatedArea());
            }
        }

        public void figureHandlesChanged(FigureEvent e) {
        }

        public void figureChanged(FigureEvent e) {
            repaintDrawingArea(e.getInvalidatedArea());
        }

        public void figureAdded(FigureEvent e) {
        }

        public void figureRemoved(FigureEvent e) {
        }

        public void figureRequestRemove(FigureEvent e) {
        }
    }
    private EventHandler eventHandler;

    /** Creates new instance. */
    public DefaultDrawingView() {
        initComponents();
        eventHandler = createEventHandler();
        setToolTipText("dummy"); // Set a dummy tool tip text to turn tooltips on

        setFocusable(true);
        addFocusListener(eventHandler);
        setTransferHandler(new DefaultDrawingViewTransferHandler());
        //setBorder(new EmptyBorder(10,10,10,10));
        setBackground(new Color(0xb0b0b0));
        setOpaque(true);
    }

    public void setBackground(Color c) {
        super.setBackground(c);
        if (c.getRGB()==0xffffff||c.getRGB()==0xffffffff) {
        new Throwable().printStackTrace();
        }
    }

    protected EventHandler createEventHandler() {
        return new EventHandler();
    }

    /** This method is called from within the constructor to
     * initialize the form.<p>
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.<p>
     * NOTE: To prevent undesired layout effects when using floating
     * text fields, the DefaultDrawingView must not use a layout manager.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        setLayout(null);
    }// </editor-fold>//GEN-END:initComponents

    public Drawing getDrawing() {
        return drawing;
    }

    @Override
    public String getToolTipText(MouseEvent evt) {
        if (getEditor() != null && getEditor().getTool() != null) {
            return getEditor().getTool().getToolTipText(this, evt);
        }
        return null;
    }

    public void setEmptyDrawingMessage(String newValue) {
        String oldValue = (emptyDrawingLabel == null) ? null : emptyDrawingLabel.getText();
        if (newValue == null) {
            emptyDrawingLabel = null;
        } else {
            emptyDrawingLabel = new JLabel(newValue);
            emptyDrawingLabel.setHorizontalAlignment(JLabel.CENTER);
        }
        firePropertyChange("emptyDrawingMessage", oldValue, newValue);
        repaint();
    }

    public String getEmptyDrawingMessage() {
        return (emptyDrawingLabel == null) ? null : emptyDrawingLabel.getText();
    }

    /**
     * Paints the drawing view.
     * Uses rendering hints for fast painting. Paints the canvasColor, the
     * grid, the drawing, the handles and the current tool.
     */
    @Override
    public void paintComponent(Graphics gr) {
        Graphics2D g = (Graphics2D) gr;

        // Set rendering hints for speed
        g.setRenderingHint(RenderingHints.KEY_ALPHA_INTERPOLATION, RenderingHints.VALUE_ALPHA_INTERPOLATION_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_NORMALIZE);
        g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS, RenderingHints.VALUE_FRACTIONALMETRICS_ON);
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR);
        g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_SPEED);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

        drawBackground(g);
        drawCanvas(g);
        drawConstrainer(g);
        drawDrawing(g);
        drawHandles(g);
        drawTool(g);
    }

    /**
     * Prints the drawing view.
     * Uses high quality rendering hints for printing. Only prints the drawing.
     * Doesn't print the canvasColor, the grid, the handles and the tool.
     */
    @Override
    public void printComponent(Graphics gr) {

        Graphics2D g = (Graphics2D) gr;

        // Set rendering hints for quality
        g.setRenderingHint(RenderingHints.KEY_ALPHA_INTERPOLATION, RenderingHints.VALUE_ALPHA_INTERPOLATION_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_NORMALIZE);
        g.setRenderingHint(RenderingHints.KEY_FRACTIONALMETRICS, RenderingHints.VALUE_FRACTIONALMETRICS_ON);
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
        g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);
        drawDrawing(g);
    }

    /**
     * Returns the bounds of the canvas on the drawing view.
     * 
     * @return The current bounds of the canvas on the drawing view.
     */
    protected Rectangle getCanvasViewBounds() {
        // Position of the zero coordinate point on the view
        int x = (int) (-translate.x * scaleFactor);
        int y = (int) (-translate.y * scaleFactor);

        int w = getWidth();
        int h = getHeight();

        if (getDrawing() != null) {
            Double cw = CANVAS_WIDTH.get(getDrawing());
            Double ch = CANVAS_HEIGHT.get(getDrawing());
            if (cw != null && ch != null) {
                Point lowerRight = drawingToView(
                        new Point2D.Double(cw, ch));
                w = lowerRight.x - x;
                h = lowerRight.y - y;
            }
        }

        return new Rectangle(x, y, w, h);
    }

    /** Draws the canvas. If the {@code AttributeKeys.CANVAS_FILL_OPACITY} is
     * not fully opaque, the canvas area is filled with the background paint
     * before the {@code AttributeKeys.CANVAS_FILL_COLOR} is drawn.
     */
    protected void drawCanvas(Graphics2D g) {
        Rectangle cb = getCanvasViewBounds();

        // Retrieve the canvasColor color from the drawing
        Color canvasColor;
        if (drawing == null) {
            canvasColor = CANVAS_FILL_COLOR.getDefaultValue();
        } else {
            canvasColor = CANVAS_FILL_COLOR.get(drawing);
            if (canvasColor != null) {
                canvasColor = new Color((canvasColor.getRGB() & 0xffffff) | ((int) (CANVAS_FILL_OPACITY.get(drawing) * 255) << 24), true);
            }
        }
        if (canvasColor == null || canvasColor.getAlpha() != 255) {
            g.setPaint(getBackgroundPaint(cb.x, cb.y));
            g.fillRect(cb.x, cb.y, cb.width, cb.height);
        }
        if (canvasColor != null) {
            g.setColor(canvasColor);
            g.fillRect(cb.x, cb.y, cb.width, cb.height);
        }

    /*
    //Fill canvasColor with alternating colors to debug clipping
    rainbow = (rainbow + 10) % 360;
    g.setColor(
    new Color(Color.HSBtoRGB((float) (rainbow / 360f), 0.3f, 1.0f)));
    g.fill(g.getClipBounds());*/
    }
//int rainbow;

    protected void drawConstrainer(Graphics2D g) {
        Shape clip = g.getClip();

        Rectangle r = getCanvasViewBounds();
        g.clipRect(r.x, r.y, r.width, r.height);
        getConstrainer().draw(g, this);

        g.setClip(clip);
    }

    protected void drawDrawing(Graphics2D gr) {

        if (drawing != null) {
            if (drawing.getChildCount() == 0 && emptyDrawingLabel != null) {
                emptyDrawingLabel.setBounds(0, 0, getWidth(), getHeight());
                emptyDrawingLabel.paint(gr);
            } else {
                Graphics2D g = (Graphics2D) gr.create();
                AffineTransform tx = g.getTransform();
                tx.translate(-translate.x * scaleFactor, -translate.y * scaleFactor);
                tx.scale(scaleFactor, scaleFactor);
                g.setTransform(tx);

                drawing.setFontRenderContext(g.getFontRenderContext());
                drawing.draw(g);

                g.dispose();
            }

        }
    }

    protected void drawHandles(java.awt.Graphics2D g) {
        if (editor != null && editor.getActiveView() == this) {
            validateHandles();
            for (Handle h : getSelectionHandles()) {
                h.draw(g);
            }

            for (Handle h : getSecondaryHandles()) {
                h.draw(g);
            }

        }
    }

    protected void drawTool(Graphics2D g) {
        if (editor != null && editor.getActiveView() == this && editor.getTool() != null) {
            editor.getTool().draw(g);
        }

    }

    public void setDrawing(Drawing newValue) {
        Drawing oldValue = drawing;
        if (this.drawing != null) {
            this.drawing.removeCompositeFigureListener(eventHandler);
            this.drawing.removeFigureListener(eventHandler);
            clearSelection();

        }




        this.drawing = newValue;
        if (this.drawing != null) {
            this.drawing.addCompositeFigureListener(eventHandler);
            this.drawing.addFigureListener(eventHandler);
        }

        invalidateDimension();
        if (getParent() != null) {
            getParent().validate();
            if (getParent() instanceof JViewport) {
                JViewport vp = (JViewport) getParent();

                Rectangle2D.Double r = getDrawingArea();
                vp.setViewPosition(drawingToView(new Point2D.Double(Math.min(0, -r.x), Math.min(0, -r.y))));
            }

        }
        firePropertyChange(DRAWING_PROPERTY, oldValue, newValue);
        validateViewTranslation();

        revalidate();

        repaint();

    }

    protected void repaintDrawingArea(Rectangle2D.Double r) {
        Rectangle vr = drawingToView(r);
        vr.grow(1, 1);
        repaint(vr);
    }

    @Override
    public void invalidate() {
        invalidateDimension();
        super.invalidate();
    }

    /**
     * Adds a figure to the current selection.
     */
    public void addToSelection(Figure figure) {
        if (DEBUG) {
            System.out.println("DefaultDrawingView" + ".addToSelection(" + figure + ")");
        }

        Set<Figure> oldSelection = new HashSet<Figure>(selectedFigures);
        if (selectedFigures.add(figure)) {
            figure.addFigureListener(handleInvalidator);
            Set<Figure> newSelection = new HashSet<Figure>(selectedFigures);
            Rectangle invalidatedArea = null;
            if (handlesAreValid && getEditor() != null) {
                for (Handle h : figure.createHandles(detailLevel)) {
                    h.setView(this);
                    selectionHandles.add(h);
                    h.addHandleListener(eventHandler);
                    if (invalidatedArea == null) {
                        invalidatedArea = h.getDrawingArea();
                    } else {
                        invalidatedArea.add(h.getDrawingArea());
                    }

                }
            }
            fireSelectionChanged(oldSelection, newSelection);
            if (invalidatedArea != null) {
                repaint(invalidatedArea);
            }

        }
    }

    /**
     * Adds a collection of figures to the current selection.
     */
    public void addToSelection(Collection<Figure> figures) {
        Set<Figure> oldSelection = new HashSet<Figure>(selectedFigures);
        Set<Figure> newSelection = new HashSet<Figure>(selectedFigures);
        boolean selectionChanged = false;
        Rectangle invalidatedArea = null;
        for (Figure figure : figures) {
            if (selectedFigures.add(figure)) {
                selectionChanged = true;
                newSelection.add(figure);
                figure.addFigureListener(handleInvalidator);
                if (handlesAreValid && getEditor() != null) {
                    for (Handle h : figure.createHandles(detailLevel)) {
                        h.setView(this);
                        selectionHandles.add(h);
                        h.addHandleListener(eventHandler);
                        if (invalidatedArea == null) {
                            invalidatedArea = h.getDrawingArea();
                        } else {
                            invalidatedArea.add(h.getDrawingArea());
                        }

                    }
                }
            }
        }
        if (selectionChanged) {
            fireSelectionChanged(oldSelection, newSelection);
            if (invalidatedArea != null) {
                repaint(invalidatedArea);
            }

        }
    }

    /**
     * Removes a figure from the selection.
     */
    public void removeFromSelection(Figure figure) {
        Set<Figure> oldSelection = new HashSet<Figure>(selectedFigures);
        if (selectedFigures.remove(figure)) {
            Set<Figure> newSelection = new HashSet<Figure>(selectedFigures);
            invalidateHandles();

            figure.removeFigureListener(handleInvalidator);
            fireSelectionChanged(oldSelection, newSelection);
            repaint();

        }




    }

    /**
     * If a figure isn't selected it is added to the selection.
     * Otherwise it is removed from the selection.
     */
    public void toggleSelection(Figure figure) {
        if (selectedFigures.contains(figure)) {
            removeFromSelection(figure);
        } else {
            addToSelection(figure);
        }

    }

    @Override
    public void setEnabled(boolean b) {
        super.setEnabled(b);
        setCursor(Cursor.getPredefinedCursor(b ? Cursor.DEFAULT_CURSOR : Cursor.WAIT_CURSOR));
    }

    /**
     * Selects all selectable figures.
     */
    public void selectAll() {
        Set<Figure> oldSelection = new HashSet<Figure>(selectedFigures);
        selectedFigures.clear();

        for (Figure figure : drawing.getChildren()) {
            if (figure.isSelectable()) {
                selectedFigures.add(figure);
            }

        }

        Set<Figure> newSelection = new HashSet<Figure>(selectedFigures);
        invalidateHandles();

        fireSelectionChanged(oldSelection, newSelection);
        repaint();

    }

    /**
     * Clears the current selection.
     */
    public void clearSelection() {
        if (getSelectionCount() > 0) {
            Set<Figure> oldSelection = new HashSet<Figure>(selectedFigures);
            selectedFigures.clear();
            Set<Figure> newSelection = new HashSet<Figure>(selectedFigures);
            invalidateHandles();

            fireSelectionChanged(oldSelection, newSelection);
        }
//repaintDrawingArea();

    }

    /**
     * Test whether a given figure is selected.
     */
    public boolean isFigureSelected(Figure checkFigure) {
        return selectedFigures.contains(checkFigure);
    }

    /**
     * Gets the current selection as a FigureSelection. A FigureSelection
     * can be cut, copied, pasted.
     */
    public Set<Figure> getSelectedFigures() {
        return Collections.unmodifiableSet(selectedFigures);
    }

    /**
     * Gets the number of selected figures.
     */
    public int getSelectionCount() {
        return selectedFigures.size();
    }

    /**
     * Gets the currently active selection handles.
     */
    private java.util.List<Handle> getSelectionHandles() {
        validateHandles();
        return Collections.unmodifiableList(selectionHandles);
    }

    /**
     * Gets the currently active secondary handles.
     */
    private java.util.List<Handle> getSecondaryHandles() {
        validateHandles();
        return Collections.unmodifiableList(secondaryHandles);
    }

    /**
     * Invalidates the handles.
     */
    private void invalidateHandles() {
        if (handlesAreValid) {
            handlesAreValid = false;

            Rectangle invalidatedArea = null;
            for (Handle handle : selectionHandles) {
                handle.removeHandleListener(eventHandler);
                if (invalidatedArea == null) {
                    invalidatedArea = handle.getDrawingArea();
                } else {
                    invalidatedArea.add(handle.getDrawingArea());
                }

                handle.dispose();
            }

            for (Handle handle : secondaryHandles) {
                handle.removeHandleListener(eventHandler);
                if (invalidatedArea == null) {
                    invalidatedArea = handle.getDrawingArea();
                } else {
                    invalidatedArea.add(handle.getDrawingArea());
                }

                handle.dispose();
            }

            selectionHandles.clear();
            secondaryHandles.clear();
            setActiveHandle(null);
            if (invalidatedArea != null) {
                repaint(invalidatedArea);
            }

        }
    }

    /**
     * Validates the handles.
     */
    private void validateHandles() {
        // Validate handles only, if they are invalid, and if
        // the DrawingView has a DrawingEditor.
        if (!handlesAreValid && getEditor() != null) {
            handlesAreValid = true;
            selectionHandles.clear();
            Rectangle invalidatedArea = null;
            int level = detailLevel;
            do {
                for (Figure figure : getSelectedFigures()) {
                    for (Handle handle : figure.createHandles(level)) {
                        handle.setView(this);
                        selectionHandles.add(handle);
                        handle.addHandleListener(eventHandler);
                        if (invalidatedArea == null) {
                            invalidatedArea = handle.getDrawingArea();
                        } else {
                            invalidatedArea.add(handle.getDrawingArea());
                        }

                    }
                }
            } while (level-- > 0 && selectionHandles.size() == 0);
            detailLevel =
                    level + 1;

            if (invalidatedArea != null) {
                repaint(invalidatedArea);
            }

        }

    }

    /**
     * Finds a handle at a given coordinates.
     * @return A handle, null if no handle is found.
     */
    public Handle findHandle(
            Point p) {
        validateHandles();

        for (Handle handle : new ReversedList<Handle>(getSecondaryHandles())) {
            if (handle.contains(p)) {
                return handle;
            }

        }
        for (Handle handle : new ReversedList<Handle>(getSelectionHandles())) {
            if (handle.contains(p)) {
                return handle;
            }

        }
        return null;
    }

    /**
     * Gets compatible handles.
     * @return A collection containing the handle and all compatible handles.
     */
    public Collection<Handle> getCompatibleHandles(Handle master) {
        validateHandles();

        HashSet<Figure> owners = new HashSet<Figure>();
        LinkedList<Handle> compatibleHandles = new LinkedList<Handle>();
        owners.add(master.getOwner());
        compatibleHandles.add(master);

        for (Handle handle : getSelectionHandles()) {
            if (!owners.contains(handle.getOwner()) && handle.isCombinableWith(master)) {
                owners.add(handle.getOwner());
                compatibleHandles.add(handle);
            }

        }
        return compatibleHandles;

    }

    /**
     * Finds a figure at a given coordinates.
     * @return A figure, null if no figure is found.
     */
    public Figure findFigure(
            Point p) {
        return getDrawing().findFigure(viewToDrawing(p));
    }

    public Collection<Figure> findFigures(Rectangle r) {
        return getDrawing().findFigures(viewToDrawing(r));
    }

    public Collection<Figure> findFiguresWithin(Rectangle r) {
        return getDrawing().findFiguresWithin(viewToDrawing(r));
    }

    public void addFigureSelectionListener(FigureSelectionListener fsl) {
        listenerList.add(FigureSelectionListener.class, fsl);
    }

    public void removeFigureSelectionListener(FigureSelectionListener fsl) {
        listenerList.remove(FigureSelectionListener.class, fsl);
    }

    /**
     *  Notify all listenerList that have registered interest for
     * notification on this event type.
     */
    protected void fireSelectionChanged(
            Set<Figure> oldValue,
            Set<Figure> newValue) {
        if (listenerList.getListenerCount() > 0) {
            FigureSelectionEvent event = null;
            // Notify all listeners that have registered interest for
            // Guaranteed to return a non-null array
            Object[] listeners = listenerList.getListenerList();
            // Process the listeners last to first, notifying
            // those that are interested in this event
            for (int i = listeners.length - 2; i >=
                    0; i -=
                            2) {
                if (listeners[i] == FigureSelectionListener.class) {
                    // Lazily create the event:
















                    if (event == null) {
                        event = new FigureSelectionEvent(this, oldValue, newValue);
                    }
                    ((FigureSelectionListener) listeners[i + 1]).selectionChanged(event);
                }
            }

        }
    }

    protected void invalidateDimension() {
        cachedPreferredSize = null;
        cachedDrawingArea =
                null;
    }

    public Constrainer getConstrainer() {
        return isConstrainerVisible() ? visibleConstrainer : invisibleConstrainer;
    }

    @Override
    public Dimension getPreferredSize() {
        if (cachedPreferredSize == null) {
            Rectangle2D.Double r = getDrawingArea();
            Double cw = getDrawing() == null ? null : CANVAS_WIDTH.get(getDrawing());
            Double ch = getDrawing() == null ? null : CANVAS_HEIGHT.get(getDrawing());
            Insets insets = getInsets();
            if (cw == null || ch == null) {
                cachedPreferredSize = new Dimension(
                        (int) ((Math.max(0, r.x) + r.width) * scaleFactor) + insets.left + insets.right,
                        (int) ((Math.max(0, r.y) + r.height) * scaleFactor) + insets.top + insets.bottom);
            } else {
                cachedPreferredSize = new Dimension(
                        (int) (Math.max((Math.max(0, r.x) + r.width), cw) * scaleFactor) + insets.left + insets.right,
                        (int) (Math.max((Math.max(0, r.y) + r.height), ch) * scaleFactor) + insets.top + insets.bottom);
            }

            validateViewTranslation();
        }

        return (Dimension) cachedPreferredSize.clone();
    }

    protected Rectangle2D.Double getDrawingArea() {
        if (cachedDrawingArea == null) {
            if (drawing != null) {
                cachedDrawingArea = drawing.getDrawingArea();
            } else {
                cachedDrawingArea = new Rectangle2D.Double();
            }

        }
        return (Rectangle2D.Double) cachedDrawingArea.clone();
    }

    /**
     * Side effect: Changes view Translation.
     */
    @Override
    public void setBounds(int x, int y, int width, int height) {
        super.setBounds(x, y, width, height);
        validateViewTranslation();

    }

    /**
     * Updates the view translation taking into account the current dimension
     * of the view JComponent, the size of the drawing, and the scale factor.
     */
    private void validateViewTranslation() {
        if (getDrawing() == null) {
            translate.x = translate.y = 0;
            return;

        }





        Point2D.Double oldTranslate = (Point2D.Double) translate.clone();

        int width = getWidth();
        int height = getHeight();
        Insets insets = getInsets();
        Rectangle2D.Double r = getDrawingArea();
        Double cw = CANVAS_WIDTH.get(getDrawing());
        Double ch = CANVAS_HEIGHT.get(getDrawing());

        if (cw == null || ch == null) {
            // The canvas size is not specified. 

            // Place the drawing at the top left corner.
            translate.x = Math.min(0, r.x);
            translate.y = Math.min(0, r.y);
        } else {
            // The canvas size is not specified.

            //Place the canvas at the center
            Dimension preferred = getPreferredSize();
            if (cw != null && ch != null) {
                if (cw * scaleFactor < width) {
                    translate.x = (width / scaleFactor - cw) / -2d;
                }

                if (ch * scaleFactor < height) {
                    translate.y = (height / scaleFactor - ch) / -2d;
                }

            }

            if (r.y - translate.y < insets.top / scaleFactor) {
                // We cut off the upper part of the drawing -> shift the canvas down
                translate.y = r.y;
            } else if (r.y - translate.y + r.height > (height - insets.bottom) / scaleFactor) {
                // We cut off the lower part of the drawing -> shift the canvas up
                translate.y = r.y + r.height - (height - insets.bottom) / scaleFactor;
            }

            if (r.x - translate.x < insets.left / scaleFactor) {
                // We cut off the left part of the drawing -> shift the canvas right
                translate.x = r.x;
            } else if (r.x - translate.x + r.width > (width - insets.right) / scaleFactor) {
                // We cut off the right part of the drawing -> shift the canvas left
                translate.x = r.x + r.width - (width - insets.right) / scaleFactor;
            }

        }
        // Move the canvas out of the center if needed

        if (!oldTranslate.equals(translate)) {

            fireViewTransformChanged();
            repaint();

        }




    }

    /**
     * Converts drawing coordinates to view coordinates.
     */
    public Point drawingToView(
            Point2D.Double p) {
        return new Point(
                (int) ((p.x - translate.x) * scaleFactor),
                (int) ((p.y - translate.y) * scaleFactor));
    }

    /**
     * Converts view coordinates to drawing coordinates.
     */
    public Point2D.Double viewToDrawing(Point p) {
        return new Point2D.Double(
                p.x / scaleFactor + translate.x,
                p.y / scaleFactor + translate.y);
    }

    public Rectangle drawingToView(
            Rectangle2D.Double r) {
        return new Rectangle(
                (int) ((r.x - translate.x) * scaleFactor),
                (int) ((r.y - translate.y) * scaleFactor),
                (int) (r.width * scaleFactor),
                (int) (r.height * scaleFactor));
    }

    public Rectangle2D.Double viewToDrawing(Rectangle r) {
        return new Rectangle2D.Double(
                r.x / scaleFactor + translate.x,
                r.y / scaleFactor + translate.y,
                r.width / scaleFactor,
                r.height / scaleFactor);
    }

    public JComponent getComponent() {
        return this;
    }

    public double getScaleFactor() {
        return scaleFactor;
    }

    public void setScaleFactor(double newValue) {
        double oldValue = scaleFactor;
        scaleFactor =
                newValue;

        //fireViewTransformChanged();
        validateViewTranslation();

        firePropertyChange("scaleFactor", oldValue, newValue);

        invalidate();

        invalidateHandles();

        if (getParent() != null) {
            getParent().validate();
        }

        repaint();
    }

    protected void fireViewTransformChanged() {
        for (Handle handle : selectionHandles) {
            handle.viewTransformChanged();
        }

        for (Handle handle : secondaryHandles) {
            handle.viewTransformChanged();
        }

    }

    public void setHandleDetailLevel(int newValue) {
        if (newValue != detailLevel) {
            detailLevel = newValue;
            invalidateHandles();

            validateHandles();

        }






    }

    public int getHandleDetailLevel() {
        return detailLevel;
    }

    public AffineTransform getDrawingToViewTransform() {
        AffineTransform t = new AffineTransform();
        t.scale(scaleFactor, scaleFactor);
        t.translate(-translate.x, -translate.y);
        return t;
    }

    public void delete() {
        final LinkedList<CompositeFigureEvent> deletionEvents = new LinkedList<CompositeFigureEvent>();
        final java.util.List<Figure> deletedFigures = drawing.sort(getSelectedFigures());

        // Abort, if not all of the selected figures may be removed from the
        // drawing
        for (Figure f : deletedFigures) {
            if (!f.isRemovable()) {
                getToolkit().beep();
                return;

            }






        }

        // Get z-indices of deleted figures
        final int[] deletedFigureIndices = new int[deletedFigures.size()];
        for (int i = 0; i <
                deletedFigureIndices.length; i++) {
            deletedFigureIndices[i] = drawing.indexOf(deletedFigures.get(i));
        }

        clearSelection();
        getDrawing().removeAll(deletedFigures);

        getDrawing().fireUndoableEditHappened(new AbstractUndoableEdit() {

            @Override
            public String getPresentationName() {
                ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
                return labels.getString("edit.delete.text");
            }

            @Override
            public void undo() throws CannotUndoException {
                super.undo();
                clearSelection();

                Drawing d = getDrawing();
                for (int i = 0; i <
                        deletedFigureIndices.length; i++) {
                    d.add(deletedFigureIndices[i], deletedFigures.get(i));
                }

                addToSelection(deletedFigures);
            }

            @Override
            public void redo() throws CannotRedoException {
                super.redo();
                for (int i = 0; i <
                        deletedFigureIndices.length; i++) {
                    drawing.remove(deletedFigures.get(i));
                }

            }
        });
    }

    public void duplicate() {
        Collection<Figure> sorted = getDrawing().sort(getSelectedFigures());
        HashMap<Figure, Figure> originalToDuplicateMap = new HashMap<Figure, Figure>(sorted.size());

        clearSelection();

        final ArrayList<Figure> duplicates = new ArrayList<Figure>(sorted.size());
        AffineTransform tx = new AffineTransform();
        tx.translate(5, 5);
        for (Figure f : sorted) {
            Figure d = (Figure) f.clone();
            d.transform(tx);
            duplicates.add(d);
            originalToDuplicateMap.put(f, d);
            drawing.add(d);
        }

        for (Figure f : duplicates) {
            f.remap(originalToDuplicateMap, false);
        }

        addToSelection(duplicates);

        getDrawing().fireUndoableEditHappened(new AbstractUndoableEdit() {

            @Override
            public String getPresentationName() {
                ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.draw.Labels");
                return labels.getString("edit.duplicate.text");
            }

            @Override
            public void undo() throws CannotUndoException {
                super.undo();
                getDrawing().removeAll(duplicates);
            }

            @Override
            public void redo() throws CannotRedoException {
                super.redo();
                getDrawing().addAll(duplicates);
            }
        });
    }

    public void removeNotify(DrawingEditor editor) {
        this.editor = null;
        repaint();

    }

    public void addNotify(DrawingEditor editor) {
        DrawingEditor oldValue = editor;
        this.editor = editor;
        firePropertyChange("editor", oldValue, editor);
        invalidateHandles();

        repaint();

    }

    public void setVisibleConstrainer(Constrainer newValue) {
        Constrainer oldValue = visibleConstrainer;
        visibleConstrainer =
                newValue;
        firePropertyChange(VISIBLE_CONSTRAINER_PROPERTY, oldValue, newValue);
    }

    public Constrainer getVisibleConstrainer() {
        return visibleConstrainer;
    }

    public void setInvisibleConstrainer(Constrainer newValue) {
        Constrainer oldValue = invisibleConstrainer;
        invisibleConstrainer =
                newValue;
        firePropertyChange(INVISIBLE_CONSTRAINER_PROPERTY, oldValue, newValue);
    }

    public Constrainer getInvisibleConstrainer() {
        return invisibleConstrainer;
    }

    public void setConstrainerVisible(boolean newValue) {
        boolean oldValue = isConstrainerVisible;
        isConstrainerVisible =
                newValue;
        firePropertyChange(CONSTRAINER_VISIBLE_PROPERTY, oldValue, newValue);
        repaint();

    }

    public boolean isConstrainerVisible() {
        return isConstrainerVisible;
    }
    protected BufferedImage backgroundTile;

    /**
     * Returns a paint for drawing the background of the drawing area.
     * @return Paint.
     */
    protected Paint getBackgroundPaint(
            int x, int y) {
        if (backgroundTile == null) {
            backgroundTile = new BufferedImage(16, 16, BufferedImage.TYPE_INT_RGB);
            Graphics2D g = backgroundTile.createGraphics();
            g.setColor(Color.white);
            g.fillRect(0, 0, 16, 16);
            g.setColor(new Color(0xdfdfdf));
            g.fillRect(0, 0, 8, 8);
            g.fillRect(8, 8, 8, 8);
            g.dispose();
        }

        return new TexturePaint(backgroundTile,
                new Rectangle(x, y, backgroundTile.getWidth(), backgroundTile.getHeight()));
    }

    public DrawingEditor getEditor() {
        return editor;
    }
    // Variables declaration - do not modify//GEN-BEGIN:variables
    // End of variables declaration//GEN-END:variables

    public void setActiveHandle(Handle newValue) {
        Handle oldValue = activeHandle;
        if (oldValue != null) {
            repaint(oldValue.getDrawingArea());
        }

        activeHandle = newValue;
        if (newValue != null) {
            repaint(newValue.getDrawingArea());
        }

        firePropertyChange(ACTIVE_HANDLE_PROPERTY, oldValue, newValue);
    }

    public Handle getActiveHandle() {
        return activeHandle;
    }
}

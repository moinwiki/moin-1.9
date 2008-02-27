/*
 * @(#)StandardDrawingView.java 5.1
 *
 */

package CH.ifa.draw.standard;

import java.awt.*;
import java.awt.event.*;
import java.util.*;
import java.io.*;
import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;

/**
 * The standard implementation of DrawingView.
 * @see DrawingView
 * @see Painter
 * @see Tool
 */

public  class StandardDrawingView
    extends Panel
        implements DrawingView,
                   MouseListener,
                   MouseMotionListener,
                   KeyListener {

    /**
     * The DrawingEditor of the view.
     * @see #tool
     * @see #setStatus
     */
    transient private DrawingEditor   fEditor;

    /**
     * The shown drawing.
     */
    private Drawing         fDrawing;

    /**
     * the accumulated damaged area
     */
    private transient Rectangle fDamage = null;

    /**
     * The list of currently selected figures.
     */
    transient private Vector fSelection;

    /**
     * The shown selection handles.
     */
    transient private Vector fSelectionHandles;

    /**
     * The preferred size of the view
     */
    private Dimension fViewSize;

    /**
     * The position of the last mouse click
     * inside the view.
     */
    private Point fLastClick;

    /**
     * A vector of optional backgrounds. The vector maintains
     * a list a view painters that are drawn before the contents,
     * that is in the background.
     */
    private Vector fBackgrounds = null;

    /**
     * A vector of optional foregrounds. The vector maintains
     * a list a view painters that are drawn after the contents,
     * that is in the foreground.
     */
    private Vector fForegrounds = null;

    /**
     * The update strategy used to repair the view.
     */
    private Painter fUpdateStrategy;

    /**
     * The grid used to constrain points for snap to
     * grid functionality.
     */
    private PointConstrainer fConstrainer;

    private boolean showGuides;

    /*
     * Serialization support. In JavaDraw only the Drawing is serialized.
     * However, for beans support StandardDrawingView supports
     * serialization
     */
    private static final long serialVersionUID = -3878153366174603336L;
    private int drawingViewSerializedDataVersion = 1;

    /**
     * Constructs the view.
     */
    public StandardDrawingView(DrawingEditor editor, int width, int height) {
        fEditor = editor;
        fViewSize = new Dimension(width,height);
        fLastClick = new Point(0, 0);
        fConstrainer = null;
        fSelection = new Vector();
	showGuides = true;
        setDisplayUpdate(new BufferedUpdateStrategy());
        setBackground(Color.lightGray);

        addMouseListener(this);
        addMouseMotionListener(this);
        addKeyListener(this);
    }

    /**
     * Sets the view's editor.
     */
    public void setEditor(DrawingEditor editor) {
        fEditor = editor;
    }

    /**
     * Gets the current tool.
     */
    public Tool tool() {
        return fEditor.tool();
    }

    /**
     * Gets the drawing.
     */
    public Drawing drawing() {
        return fDrawing;
    }

    /**
     * Sets and installs another drawing in the view.
     */
    public void setDrawing(Drawing d) {
        clearSelection();

        if (fDrawing != null)
            fDrawing.removeDrawingChangeListener(this);

        fDrawing = d;
        if (fDrawing != null)
            fDrawing.addDrawingChangeListener(this);
        checkMinimumSize();
        repaint();
    }

    /**
     * Gets the editor.
     */
    public DrawingEditor editor() {
        return fEditor;
    }

    /**
     * Adds a figure to the drawing.
     * @return the added figure.
     */
    public Figure add(Figure figure) {
        return drawing().add(figure);
    }

    /**
     * Removes a figure from the drawing.
     * @return the removed figure
     */
    public Figure remove(Figure figure) {
        return drawing().remove(figure);
    }

    /**
     * Adds a vector of figures to the drawing.
     */
    public void addAll(Vector figures) {
        FigureEnumeration k = new FigureEnumerator(figures);
        while (k.hasMoreElements())
            add(k.nextFigure());
    }

    /**
     * Gets the minimum dimension of the drawing.
     */
    public Dimension getMinimumSize() {
        return fViewSize;
    }

    /**
     * Gets the preferred dimension of the drawing..
     */
    public Dimension getPreferredSize() {
        return getMinimumSize();
    }

    /**
     * Sets the current display update strategy.
     * @see UpdateStrategy
     */
    public void setDisplayUpdate(Painter updateStrategy) {
        fUpdateStrategy = updateStrategy;
    }

    /**
     * Gets the currently selected figures.
     * @return a vector with the selected figures. The vector
     * is a copy of the current selection.
     */
    public Vector selection() {
        // protect the vector with the current selection
        return (Vector)fSelection.clone();
    }

    /**
     * Gets an enumeration over the currently selected figures.
     */
    public FigureEnumeration selectionElements() {
        return new FigureEnumerator(fSelection);
    }

    /**
     * Gets the currently selected figures in Z order.
     * @see #selection
     * @return a vector with the selected figures. The vector
     * is a copy of the current selection.
     */
    public Vector selectionZOrdered() {
        Vector result = new Vector(fSelection.size());
        FigureEnumeration figures = drawing().figures();

        while (figures.hasMoreElements()) {
            Figure f= figures.nextFigure();
            if (fSelection.contains(f)) {
                result.addElement(f);
            }
        }
        return result;
    }

    /**
     * Gets the number of selected figures.
     */
    public int selectionCount() {
        return fSelection.size();
    }

    /**
     * Adds a figure to the current selection.
     */
    public void addToSelection(Figure figure) {
        if (!fSelection.contains(figure)) {
            fSelection.addElement(figure);
            fSelectionHandles = null;
            figure.invalidate();
            selectionChanged();
        }
    }

    /**
     * Adds a vector of figures to the current selection.
     */
    public void addToSelectionAll(Vector figures) {
        FigureEnumeration k = new FigureEnumerator(figures);
        while (k.hasMoreElements())
            addToSelection(k.nextFigure());
    }

    /**
     * Removes a figure from the selection.
     */
    public void removeFromSelection(Figure figure) {
        if (fSelection.contains(figure)) {
            fSelection.removeElement(figure);
            fSelectionHandles = null;
            figure.invalidate();
            selectionChanged();
        }
    }

    /**
     * If a figure isn't selected it is added to the selection.
     * Otherwise it is removed from the selection.
     */
    public void toggleSelection(Figure figure) {
        if (fSelection.contains(figure))
            removeFromSelection(figure);
        else
            addToSelection(figure);
        selectionChanged();
    }

    /**
     * Clears the current selection.
     */
    public void clearSelection() {
        Figure figure;

        FigureEnumeration k = selectionElements();

        while (k.hasMoreElements())
            k.nextFigure().invalidate();
        fSelection = new Vector();
        fSelectionHandles = null;
        selectionChanged();
    }

    /**
     * Gets an enumeration of the currently active handles.
     */
    private Enumeration selectionHandles() {
        if (fSelectionHandles == null) {
            fSelectionHandles = new Vector();
            FigureEnumeration k = selectionElements();
            while (k.hasMoreElements()) {
                Figure figure = k.nextFigure();
                Enumeration kk = figure.handles().elements();
                while (kk.hasMoreElements())
                    fSelectionHandles.addElement(kk.nextElement());
            }
        }
        return fSelectionHandles.elements();
    }

    /**
     * Gets the current selection as a FigureSelection. A FigureSelection
     * can be cut, copied, pasted.
     */
    public FigureSelection getFigureSelection() {
        return new FigureSelection(selectionZOrdered());
    }

    /**
     * Move current selection by dx and dy
     */
    public void moveSelection(int dx, int dy) {
        FigureEnumeration figures = selectionElements();
        while (figures.hasMoreElements()) {
            Figure fig = figures.nextFigure();
            Figure obsrvd = (Figure) fig.getAttribute("observed.figure");
            if (obsrvd == null || !figures.contains(obsrvd)){
                fig.moveBy(dx, dy);
            }
        }
        checkDamage();
    }

    /**
     * Finds a handle at the given coordinates.
     * @return the hit handle, null if no handle is found.
     */
    public Handle findHandle(int x, int y) {
        Handle handle;

        Enumeration k = selectionHandles();
        while (k.hasMoreElements()) {
            handle = (Handle) k.nextElement();
            if (handle.containsPoint(x, y))
                return handle;
        }
        return null;
    }

    /**
     * Informs that the current selection changed.
     * By default this event is forwarded to the
     * drawing editor.
     */
    protected void selectionChanged() {
        fEditor.selectionChanged(this);
    }

    /**
     * Gets the position of the last click inside the view.
     */
    public Point lastClick() {
        return fLastClick;
    }

    /**
     * Sets the grid spacing that is used to constrain points.
     */
    public void setConstrainer(PointConstrainer c) {
        fConstrainer = c;
    }

    /**
     * Gets the current constrainer.
     */
    public PointConstrainer getConstrainer() {
        return fConstrainer;
    }

    /**
     * Constrains a point to the current grid.
     */
    protected Point constrainPoint(Point p) {
        // constrin to view size
        Dimension size = getSize();
        //p.x = Math.min(size.width, Math.max(1, p.x));
        //p.y = Math.min(size.height, Math.max(1, p.y));
        p.x = Geom.range(1, size.width, p.x);
        p.y = Geom.range(1, size.height, p.y);

        if (fConstrainer != null )
            return fConstrainer.constrainPoint(p);
        return p;
	}

    /**
     * Handles mouse down events. The event is delegated to the
     * currently active tool.
     * @return whether the event was handled.
     */
    public void mousePressed(MouseEvent e) {
        requestFocus(); // JDK1.1
        Point p = constrainPoint(new Point(e.getX(), e.getY()));
        fLastClick = new Point(e.getX(), e.getY());
        tool().mouseDown(e, p.x, p.y);
        checkDamage();
    }

    /**
     * Handles mouse drag events. The event is delegated to the
     * currently active tool.
     * @return whether the event was handled.
     */
    public void mouseDragged(MouseEvent e) {
        Point p = constrainPoint(new Point(e.getX(), e.getY()));
        tool().mouseDrag(e, p.x, p.y);
        checkDamage();
    }

    /**
     * Handles mouse move events. The event is delegated to the
     * currently active tool.
     * @return whether the event was handled.
     */
    public void mouseMoved(MouseEvent e) {
        tool().mouseMove(e, e.getX(), e.getY());
    }

    /**
     * Handles mouse up events. The event is delegated to the
     * currently active tool.
     * @return whether the event was handled.
     */
    public void mouseReleased(MouseEvent e) {
        Point p = constrainPoint(new Point(e.getX(), e.getY()));
        tool().mouseUp(e, p.x, p.y);
        checkDamage();
	checkMinimumSize();
    }

    /**
     * Handles key down events. Cursor keys are handled
     * by the view the other key events are delegated to the
     * currently active tool.
     * @return whether the event was handled.
     */
    public void keyPressed(KeyEvent e) {
        int code = e.getKeyCode();
        if ((code == KeyEvent.VK_BACK_SPACE) || (code == KeyEvent.VK_DELETE)) {
            Command cmd = new DeleteCommand("Delete", this);
            cmd.execute();
        } else if (code == KeyEvent.VK_DOWN || code == KeyEvent.VK_UP ||
            code == KeyEvent.VK_RIGHT || code == KeyEvent.VK_LEFT) {
            handleCursorKey(code);
        } else {
            tool().keyDown(e, code);
        }
        checkDamage();
    }

    /**
     * Handles cursor keys by moving all the selected figures
     * one grid point in the cursor direction.
     */
    protected void handleCursorKey(int key) {
        int dx = 0, dy = 0;
        int stepX = 1, stepY = 1;
        // should consider Null Object.
        if (fConstrainer != null) {
            stepX = fConstrainer.getStepX();
            stepY = fConstrainer.getStepY();
        }

        switch (key) {
        case KeyEvent.VK_DOWN:
            dy = stepY;
            break;
        case KeyEvent.VK_UP:
            dy = -stepY;
            break;
        case KeyEvent.VK_RIGHT:
            dx = stepX;
            break;
        case KeyEvent.VK_LEFT:
            dx = -stepX;
            break;
        }
        moveSelection(dx, dy);
    }

    /**
     * Refreshes the drawing if there is some accumulated damage
     */
    public synchronized void checkDamage() {
        Enumeration each = drawing().drawingChangeListeners();
        while (each.hasMoreElements()) {
            Object l = each.nextElement();
            if (l instanceof DrawingView) {
                ((DrawingView)l).repairDamage();
            }
        }
    }

    public void repairDamage() {
        if (fDamage != null) {
            repaint(fDamage.x, fDamage.y, fDamage.width, fDamage.height);
            fDamage = null;
        }
    }

    public void drawingInvalidated(DrawingChangeEvent e) {
        Rectangle r = e.getInvalidatedRectangle();
        if (fDamage == null)
            fDamage = r;
        else
            fDamage.add(r);
    }

    public void drawingRequestUpdate(DrawingChangeEvent e) {
        repairDamage();
    }

    /**
     * Updates the drawing view.
     */
    public void update(Graphics g) {
        paint(g);
    }

    /**
     * Paints the drawing view. The actual drawing is delegated to
     * the current update strategy.
     * @see Painter
     */
    public void paint(Graphics g) {
        fUpdateStrategy.draw(g, this);
    }

    /**
     * Draws the contents of the drawing view.
     * The view has three layers: background, drawing, handles.
     * The layers are drawn in back to front order.
     */
    public void drawAll(Graphics g) {
	boolean isPrinting = (g instanceof PrintGraphics);
        drawBackground(g);
        if (fBackgrounds != null && !isPrinting)
            drawPainters(g, fBackgrounds);
        drawDrawing(g, showGuides);
        if (fForegrounds != null && !isPrinting)
            drawPainters(g, fForegrounds);
        if (!isPrinting)
            drawHandles(g);
    }

    /**
     * Draws the currently active handles.
     */
    public void drawHandles(Graphics g) {
        Enumeration k = selectionHandles();
        while (k.hasMoreElements())
            ((Handle) k.nextElement()).draw(g);
    }

    /**
     * Draws the drawing.
     */
    public void drawDrawing(Graphics g, boolean showGuides) {
        fDrawing.draw(g, showGuides);
    }

    /**
     * Draws the background. If a background pattern is set it
     * is used to fill the background. Otherwise the background
     * is filled in the background color.
     */
    public void drawBackground(Graphics g) {
        g.setColor(getBackground());
        g.fillRect(0, 0, getBounds().width, getBounds().height);
    }

    private void drawPainters(Graphics g, Vector v) {
        for (int i = 0; i < v.size(); i++)
            ((Painter)v.elementAt(i)).draw(g, this);
    }

    /**
     * Adds a background.
     */
    public void addBackground(Painter painter)  {
        if (fBackgrounds == null)
            fBackgrounds = new Vector(3);
        fBackgrounds.addElement(painter);
        repaint();
    }

    /**
     * Removes a background.
     */
    public void removeBackground(Painter painter)  {
        if (fBackgrounds != null)
            fBackgrounds.removeElement(painter);
        repaint();
    }

    /**
     * Removes a foreground.
     */
    public void removeForeground(Painter painter)  {
        if (fForegrounds != null)
            fForegrounds.removeElement(painter);
        repaint();
    }

    /**
     * Adds a foreground.
     */
    public void addForeground(Painter painter)  {
        if (fForegrounds == null)
            fForegrounds = new Vector(3);
        fForegrounds.addElement(painter);
        repaint();
    }

    /**
     * Freezes the view by acquiring the drawing lock.
     * @see Drawing#lock
     */
    public void freezeView() {
        drawing().lock();
    }

    /**
     * Unfreezes the view by releasing the drawing lock.
     * @see Drawing#unlock
     */
    public void unfreezeView() {
        drawing().unlock();
    }

    private void readObject(ObjectInputStream s)
        throws ClassNotFoundException, IOException {

        s.defaultReadObject();

        fSelection = new Vector(); // could use lazy initialization instead
        if (fDrawing != null)
            fDrawing.addDrawingChangeListener(this);
    }

    private Dimension getDrawingSize() {
        FigureEnumeration k = drawing().figures();
        Dimension d = new Dimension(0, 0);
        while (k.hasMoreElements()) {
            Rectangle r = k.nextFigure().displayBox();
            d.width = Math.max(d.width, r.x+r.width);
            d.height = Math.max(d.height, r.y+r.height);
        }
	return d;
    }

    /**
     * Bloat the drawing if necessary to contain all objects. Do not
     * shrink it, though!
     */
    private void checkMinimumSize() {
        Dimension d = getDrawingSize();
	boolean bloat = false;
        if (fViewSize.height < d.height) {
            fViewSize.height = d.height+10;
	    bloat = true;
	}
	if (fViewSize.width < d.width) {
            fViewSize.width = d.width+10;
	    bloat = true;
	}
	if (bloat)
            setSize(fViewSize);
    }

    public boolean isFocusTraversable() {
        return true;
    }

    public void enableGuides(boolean enable) {
	showGuides = enable;
    }

    public boolean guidesEnabled() {
	return showGuides;
    }

    // listener methods we are not interested in
    public void mouseEntered(MouseEvent e) {}
    public void mouseExited(MouseEvent e) {}
    public void mouseClicked(MouseEvent e) {}
    public void keyTyped(KeyEvent e) {}
    public void keyReleased(KeyEvent e) {}
}

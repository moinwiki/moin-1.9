/*
 * @(#)DrawingView.java 5.1
 *
 */

package CH.ifa.draw.framework;

import java.awt.image.ImageObserver;
import java.awt.*;
import java.util.*;
import java.io.*;
import CH.ifa.draw.util.*;

/**
 * DrawingView renders a Drawing and listens to its changes.
 * It receives user input and delegates it to the current tool.
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld026.htm>Observer</a></b><br>
 * DrawingView observes drawing for changes via the DrawingListener interface.<br>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld032.htm>State</a></b><br>
 * DrawingView plays the role of the StateContext in
 * the State pattern. Tool is the State.<br>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld034.htm>Strategy</a></b><br>
 * DrawingView is the StrategyContext in the Strategy pattern
 * with regard to the UpdateStrategy. <br>
 * DrawingView is the StrategyContext for the PointConstrainer.
 *
 * @see Drawing
 * @see Painter
 * @see Tool
 */


public interface DrawingView extends ImageObserver, DrawingChangeListener {

    /**
     * Sets the view's editor.
     */
    public void setEditor(DrawingEditor editor);

    /**
     * Gets the current tool.
     */
    public Tool tool();

    /**
     * Gets the drawing.
     */
    public Drawing drawing();

    public void enableGuides(boolean enable);

    public boolean guidesEnabled();

    /**
     * Sets and installs another drawing in the view.
     */
    public void setDrawing(Drawing d);

    /**
     * Gets the editor.
     */
    public DrawingEditor editor();

    /**
     * Adds a figure to the drawing.
     * @return the added figure.
     */
    public Figure add(Figure figure);

    /**
     * Removes a figure from the drawing.
     * @return the removed figure
     */
    public Figure remove(Figure figure);

    /**
     * Adds a vector of figures to the drawing.
     */
    public void addAll(Vector figures);

    /**
     * Gets the size of the drawing.
     */
    public Dimension getSize();

    /**
     * Gets the minimum dimension of the drawing.
     */
    public Dimension getMinimumSize();

    /**
     * Gets the preferred dimension of the drawing..
     */
    public Dimension getPreferredSize();

    /**
     * Sets the current display update strategy.
     * @see UpdateStrategy
     */
    public void setDisplayUpdate(Painter updateStrategy);

    /**
     * Gets the currently selected figures.
     * @return a vector with the selected figures. The vector
     * is a copy of the current selection.
     */
    public Vector selection();

    /**
     * Gets an enumeration over the currently selected figures.
     */
    public FigureEnumeration selectionElements();

    /**
     * Gets the currently selected figures in Z order.
     * @see #selection
     * @return a vector with the selected figures. The vector
     * is a copy of the current selection.
     */
    public Vector selectionZOrdered();

    /**
     * Gets the number of selected figures.
     */
    public int selectionCount();

    /**
     * Adds a figure to the current selection.
     */
    public void addToSelection(Figure figure);

    /**
     * Adds a vector of figures to the current selection.
     */
    public void addToSelectionAll(Vector figures);

    /**
     * Removes a figure from the selection.
     */
    public void removeFromSelection(Figure figure);

    /**
     * If a figure isn't selected it is added to the selection.
     * Otherwise it is removed from the selection.
     */
    public void toggleSelection(Figure figure);

    /**
     * Clears the current selection.
     */
    public void clearSelection();

    /**
     * Gets the current selection as a FigureSelection. A FigureSelection
     * can be cut, copied, pasted.
     */
    public FigureSelection getFigureSelection();

    /**
     * Move current selection by dx and dy
     */
    public void moveSelection(int dx, int dy);

    /**
     * Finds a handle at the given coordinates.
     * @return the hit handle, null if no handle is found.
     */
    public Handle findHandle(int x, int y);

    /**
     * Gets the position of the last click inside the view.
     */
    public Point lastClick();

    /**
     * Sets the current point constrainer.
     */
    public void setConstrainer(PointConstrainer p);

    /**
     * Gets the current grid setting.
     */
    public PointConstrainer getConstrainer();

    /**
     * Checks whether the drawing has some accumulated damage
     */
    public void checkDamage();

    /**
     * Repair the damaged area
     */
    public void repairDamage();

    /**
     * Paints the drawing view. The actual drawing is delegated to
     * the current update strategy.
     * @see Painter
     */
    public void paint(Graphics g);

    /**
     * Creates an image with the given dimensions
     */
    public Image createImage(int width, int height);

    /**
     * Gets a graphic to draw into
     */
    public Graphics getGraphics();

    /**
     * Gets the background color of the DrawingView
     */
    public Color getBackground();

    /**
     * Gets the background color of the DrawingView
     */
    public void setBackground(Color c);

    /**
     * Draws the contents of the drawing view.
     * The view has three layers: background, drawing, handles.
     * The layers are drawn in back to front order.
     */
    public void drawAll(Graphics g);

    /**
     * Draws the currently active handles.
     */
    public void drawHandles(Graphics g);

    /**
     * Draws the drawing.
     */
    public void drawDrawing(Graphics g, boolean showGuides);

    /**
     * Draws the background. If a background pattern is set it
     * is used to fill the background. Otherwise the background
     * is filled in the background color.
     */
    public void drawBackground(Graphics g);

    /**
     * Sets the cursor of the DrawingView
     */
    public void setCursor(Cursor c);

    /**
     * Freezes the view by acquiring the drawing lock.
     * @see Drawing#lock
     */
    public void freezeView();

    /**
     * Unfreezes the view by releasing the drawing lock.
     * @see Drawing#unlock
     */
    public void unfreezeView();
}

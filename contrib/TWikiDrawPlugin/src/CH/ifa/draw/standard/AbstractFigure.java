/*
 * @(#)AbstractFigure.java 5.1
 *
 */

package CH.ifa.draw.standard;

import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;

import java.awt.*;
import java.util.*;
import java.io.*;

/**
 * AbstractFigure provides default implementations for
 * the Figure interface.
 *
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld036.htm>Template Method</a></b><br>
 * Template Methods implement default and invariant behavior for
 * figure subclasses.
 * <hr>
 *
 * @see Figure
 * @see Handle
 */

public abstract class AbstractFigure implements Figure {

    /**
     * The attributes of a figure. Each figure can have
     * an open ended set of attributes. Attributes are
     * identified by name.
     * @see #getAttribute
     * @see #setAttribute
     */
    private FigureAttributes        fAttributes;

    /**
     * The listeners for a figure's changes.
     * @see #invalidate
     * @see #changed
     * @see #willChange
     */
    private transient FigureChangeListener fListener;

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = -10857585979273442L;
    private int abstractFigureSerializedDataVersion = 1;

    protected static Font dialogFont = Font.decode("dialog-PLAIN-12");

    protected AbstractFigure() { }

    /**
     * Moves the figure by the given offset.
     */
    public void moveBy(int dx, int dy) {
        willChange();
        basicMoveBy(dx, dy);
        changed();
    }

    /**
     * Moves the figure. This is the
     * method that subclassers override. Clients usually
     * call displayBox.
     * @see moveBy
     */
    protected abstract void basicMoveBy(int dx, int dy);

    /**
     * Changes the display box of a figure. Clients usually
     * call this method. It changes the display box
     * and announces the corresponding change.
     * @param origin the new origin
     * @param corner the new corner
     * @see displayBox
     */
    public void displayBox(Point origin, Point corner) {
        willChange();
        basicDisplayBox(origin, corner);
        changed();
    }

    /**
     * Sets the display box of a figure. This is the
     * method that subclassers override. Clients usually
     * call displayBox.
     * @see displayBox
     */
    public abstract void basicDisplayBox(Point origin, Point corner);

    /**
     * Gets the display box of a figure.
     */
    public abstract Rectangle displayBox();

    /**
     * Returns the handles of a Figure that can be used
     * to manipulate some of its attributes.
     * @return a Vector of handles
     * @see Handle
     */
    public abstract Vector handles();

    /**
     * Returns an Enumeration of the figures contained in this figure.
     * @see CompositeFigure
     */
    public FigureEnumeration figures() {
        Vector figures = new Vector(1);
        figures.addElement(this);
        return new FigureEnumerator(figures);
    }

    /**
     * Gets the size of the figure. A convenience method.
     */
    public Dimension size() {
        return new Dimension(displayBox().width, displayBox().height);
    }

    /**
     * Checks if the figure is empty. The default implementation returns
     * true if the width or height of its display box is < 3
     * @see Figure#isEmpty
     */
    public boolean isEmpty() {
        return (size().width < 3) || (size().height < 3);
    }

    /**
     * Returns the figure that contains the given point.
     * In contrast to containsPoint it returns its
     * innermost figure that contains the point.
     *
     * @see #containsPoint
     */
    public Figure findFigureInside(int x, int y) {
        if (containsPoint(x, y))
            return this;
        return null;
    }

    /**
     * Checks if a point is inside the figure.
     */
    public boolean containsPoint(int x, int y) {
        return displayBox().contains(x, y);
    }

    /**
     * Changes the display box of a figure. This is a
     * convenience method. Implementors should only
     * have to override basicDisplayBox
     * @see displayBox
     */
    public void displayBox(Rectangle r) {
        displayBox(new Point(r.x, r.y), new Point(r.x+r.width, r.y+r.height));
    }

    /**
     * Checks whether the given figure is contained in this figure.
     */
    public boolean includes(Figure figure) {
        return figure == this;
    }

    /**
     * Decomposes a figure into its parts. It returns a Vector
     * that contains itself.
     * @return an Enumeration for a Vector with itself as the
     * only element.
     */
    public FigureEnumeration decompose() {
        Vector figures = new Vector(1);
        figures.addElement(this);
        return new FigureEnumerator(figures);
    }

    /**
     * Sets the Figure's container and registers the container
     * as a figure change listener. A figure's container can be
     * any kind of FigureChangeListener. A figure is not restricted
     * to have a single container.
     */
    public void addToContainer(FigureChangeListener c) {
        addFigureChangeListener(c);
        invalidate();
    }

    /**
     * Removes a figure from the given container and unregisters
     * it as a change listener.
     */
    public void removeFromContainer(FigureChangeListener c) {
        invalidate();
        removeFigureChangeListener(c);
        changed();
    }

    /**
     * Adds a listener for this figure.
     */
    public void addFigureChangeListener(FigureChangeListener l) {
        fListener = FigureChangeEventMulticaster.add(fListener, l);
    }

    /**
     * Removes a listener for this figure.
     */
    public void removeFigureChangeListener(FigureChangeListener l) {
        fListener = FigureChangeEventMulticaster.remove(fListener, l);
    }

    /**
     * Gets the figure's listners.
     */
    public FigureChangeListener listener() {
        return fListener;
    }

    /**
     * A figure is released from the drawing. You never call this
     * method directly. Release notifies its listeners.
     * @see Figure#release
     */
    public void release() {
        if (fListener != null)
            fListener.figureRemoved(new FigureChangeEvent(this));
    }

    /**
     * Invalidates the figure. This method informs the listeners
     * that the figure's current display box is invalid and should be
     * refreshed.
     */
    public void invalidate() {
        if (fListener != null) {
            Rectangle r = displayBox();
            r.grow(Handle.HANDLESIZE, Handle.HANDLESIZE);
            fListener.figureInvalidated(new FigureChangeEvent(this, r));
        }
    }

    /**
     * Informes that a figure is about to change something that
     * affects the contents of its display box.
     *
     * @see Figure#willChange
     */
    public void willChange() {
        invalidate();
    }

    /**
     * Informs that a figure changed the area of its display box.
     *
     * @see FigureChangeEvent
     * @see Figure#changed
     */
    public void changed() {
        invalidate();
        if (fListener != null)
            fListener.figureChanged(new FigureChangeEvent(this));

    }

    /**
     * Gets the center of a figure. A convenice
     * method that is rarely overridden.
     */
    public Point center() {
        return Geom.center(displayBox());
    }

    /**
     * Checks if this figure can be connected. By default
     * AbstractFigures can be connected.
     */
    public boolean canConnect() {
        return true;
    }

    /**
     * Returns the connection inset. The connection inset
     * defines the area where the display box of a
     * figure can't be connected. By default the entire
     * display box can be connected.
     *
     */
    public Insets connectionInsets() {
        return new Insets(0, 0, 0, 0);
    }

    /**
     * Returns the Figures connector for the specified location.
     * By default a ChopBoxConnector is returned.
     * @see ChopBoxConnector
     */
    public Connector connectorAt(int x, int y) {
        return new ChopBoxConnector(this);
    }

    /**
     * Sets whether the connectors should be visible.
     * By default they are not visible and
     */
    public void connectorVisibility(boolean isVisible) {
    }

    /**
     * Returns the locator used to located connected text.
     */
    public Locator connectedTextLocator(Figure text) {
        return RelativeLocator.center();
    }

    /**
     * Gets a the default value for a named attribute
     * @see getAttribute
     */
    public Object defaultAttribute(String name) {
	return null;
    }

    /**
     * Returns the named attribute or null if a
     * a figure doesn't have an attribute.
     * All figures support the attribute names
     * FillColor and FrameColor
     */
    public Object getAttribute(String name) {
        if (fAttributes != null) {
            if (fAttributes.hasDefined(name))
                return fAttributes.get(name);
        }
        return defaultAttribute(name);
    }

    /**
     * Sets the named attribute to the new value
     */
    public void setAttribute(String name, Object value) {
        if (fAttributes == null)
            fAttributes = new FigureAttributes();
        fAttributes.set(name, value);
        changed();
    }

    /**
     * Clones a figure. Creates a clone by using the storable
     * mechanism to flatten the Figure to stream followed by
     * resurrecting it from the same stream.
     *
     * @see Figure#clone
     */
    public Object clone() {
        Object clone = null;
        ByteArrayOutputStream output = new ByteArrayOutputStream(200);
        try {
            ObjectOutput writer = new ObjectOutputStream(output);
            writer.writeObject(this);
            writer.close();
        } catch (IOException e) {
            System.out.println("Class not found: " + e);
        }

        InputStream input = new ByteArrayInputStream(output.toByteArray());
        try {
            ObjectInput reader = new ObjectInputStream(input);
            clone = (Object) reader.readObject();
        } catch (IOException e) {
            System.out.println(e.toString());
        }
        catch (ClassNotFoundException e) {
            System.out.println("Class not found: " + e);
        }
        return clone;
    }

    /**
     * Stores the Figure to a StorableOutput.
     */
    public void write(StorableOutput dw) {
        if (fAttributes == null)
            dw.writeString("no_attributes");
        else {
            dw.writeString("attributes");
            fAttributes.write(dw);
        }
    }

    /**
     * Reads the Figure from a StorableInput.
     */
    public void read(StorableInput dr) throws IOException {
	// test for number being next; if it's a number this is
	// an old-format file with no attributes on this figure type
	if (dr.testForNumber())
	    return;
	String s = dr.readString();
	if (s.toLowerCase().equals("attributes")) {
	    fAttributes = new FigureAttributes();
	    fAttributes.read(dr);
	}
    }
}

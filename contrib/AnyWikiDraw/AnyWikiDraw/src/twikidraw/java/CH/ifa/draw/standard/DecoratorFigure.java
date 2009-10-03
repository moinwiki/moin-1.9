/*
 * @(#)DecoratorFigure.java 5.1
 *
 */

package CH.ifa.draw.standard;

import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;

import java.awt.*;
import java.util.*;
import java.io.*;

/**
 * DecoratorFigure can be used to decorate other figures with
 * decorations like borders. Decorator forwards all the
 * methods to their contained figure. Subclasses can selectively
 * override these methods to extend and filter their behavior.
 * <hr>
 * <b>Design Patterns</b><P>
 * <img src="images/red-ball-small.gif" width=6 height=6 alt=" o ">
 * <b><a href=../pattlets/sld014.htm>Decorator</a></b><br>
 * DecoratorFigure is a decorator.
 *
 * @see Figure
 */

public abstract class DecoratorFigure
                extends AbstractFigure
                implements FigureChangeListener {

    /**
     * The decorated figure.
     */
    protected Figure fComponent;

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 8993011151564573288L;
    private int decoratorFigureSerializedDataVersion = 1;

    public DecoratorFigure() { }

    /**
     * Constructs a DecoratorFigure and decorates the passed in figure.
     */
    public DecoratorFigure(Figure figure) {
        decorate(figure);
    }

    /**
     * Forwards the connection insets to its contained figure..
     */
    public Insets connectionInsets() {
        return fComponent.connectionInsets();
    }

    /**
     * Forwards the canConnect to its contained figure..
     */
    public boolean canConnect() {
        return fComponent.canConnect();
    }

    /**
     * Forwards containsPoint to its contained figure.
     */
    public boolean containsPoint(int x, int y) {
        return fComponent.containsPoint(x, y);
    }

    /**
     * Decorates the given figure.
     */
    public void decorate(Figure figure) {
        fComponent = figure;
        fComponent.addToContainer(this);
    }

    /**
     * Removes the decoration from the contained figure.
     */
    public Figure peelDecoration() {
        fComponent.removeFromContainer(this); //??? set the container to the listener()?
        return fComponent;
    }

    /**
     * Forwards displayBox to its contained figure.
     */
    public Rectangle displayBox() {
        return fComponent.displayBox();
    }

    /**
     * Forwards basicDisplayBox to its contained figure.
     */
    public void basicDisplayBox(Point origin, Point corner) {
        fComponent.basicDisplayBox(origin, corner);
    }

    /**
     * Forwards draw to its contained figure.
     */
    public void draw(Graphics g, boolean showGuides) {
        fComponent.draw(g, showGuides);
    }

    /**
     * Forwards findFigureInside to its contained figure.
     */
    public Figure findFigureInside(int x, int y) {
        return fComponent.findFigureInside(x, y);
    }

    /**
     * Forwards handles to its contained figure.
     */
    public Vector handles() {
        return fComponent.handles();
    }

    /**
     * Forwards includes to its contained figure.
     */
    public boolean includes(Figure figure) {
        return (super.includes(figure) || fComponent.includes(figure));
    }

    /**
     * Forwards moveBy to its contained figure.
     */
    public void moveBy(int x, int y) {
        fComponent.moveBy(x, y);
    }

    /**
     * Forwards basicMoveBy to its contained figure.
     */
    protected void basicMoveBy(int x, int y) {
        // this will never be called
    }

    /**
     * Releases itself and the contained figure.
     */
    public void release() {
        super.release();
        fComponent.removeFromContainer(this);
        fComponent.release();
    }

    /**
     * Propagates invalidate up the container chain.
     * @see FigureChangeListener
     */
    public void figureInvalidated(FigureChangeEvent e) {
        if (listener() != null)
            listener().figureInvalidated(e);
    }

    public void figureChanged(FigureChangeEvent e) {
    }

    public void figureRemoved(FigureChangeEvent e) {
    }

    /**
     * Propagates figureRequestUpdate up the container chain.
     * @see FigureChangeListener
     */
    public  void figureRequestUpdate(FigureChangeEvent e) {
        if (listener() != null)
            listener().figureRequestUpdate(e);
    }

    /**
     * Propagates the removeFromDrawing request up to the container.
     * @see FigureChangeListener
     */
    public void figureRequestRemove(FigureChangeEvent e) {
        if (listener() != null)
            listener().figureRequestRemove(new FigureChangeEvent(this));
    }

    /**
     * Forwards figures to its contained figure.
     */
    public FigureEnumeration figures() {
        return fComponent.figures();
    }

    /**
     * Forwards decompose to its contained figure.
     */
    public FigureEnumeration decompose() {
        return fComponent.decompose();
    }

    /**
     * Forwards setAttribute to its contained figure.
     */
    public void setAttribute(String name, Object value) {
        fComponent.setAttribute(name, value);
    }

    /**
     * Forwards getAttribute to its contained figure.
     */
    public Object getAttribute(String name) {
        return fComponent.getAttribute(name);
    }

    /**
     * Returns the locator used to located connected text.
     */
    public Locator connectedTextLocator(Figure text) {
        return fComponent.connectedTextLocator(text);
    }

    /**
     * Returns the Connector for the given location.
     */
    public Connector connectorAt(int x, int y) {
        return fComponent.connectorAt(x, y);
    }

    /**
     * Forwards the connector visibility request to its component.
     */
    public void connectorVisibility(boolean isVisible) {
        fComponent.connectorVisibility(isVisible);
    }

    /**
     * Writes itself and the contained figure to the StorableOutput.
     */
    public void write(StorableOutput dw) {
        super.write(dw);
        dw.writeStorable(fComponent);
    }

    public String getMap() {
	return "";
    }

    /**
     * Reads itself and the contained figure from the StorableInput.
     */
    public void read(StorableInput dr) throws IOException {
        super.read(dr);
        decorate((Figure)dr.readStorable());
    }

    private void readObject(ObjectInputStream s)
        throws ClassNotFoundException, IOException {

        s.defaultReadObject();

        fComponent.addToContainer(this);
    }
}

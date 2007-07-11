/*
 * @(#)PolyLineFigure.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.util.*;
import java.io.*;
import java.net.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.util.*;

/**
 * A poly line figure consists of a list of points.
 * It has an optional line decoration at the start and end.
 *
 * @see LineDecoration
 */
public  class PolyLineFigure extends AbstractFigure {

    public final static int ARROW_TIP_NONE  = 0;
    public final static int ARROW_TIP_START = 1;
    public final static int ARROW_TIP_END   = 2;
    public final static int ARROW_TIP_BOTH  = 3;
    
    protected Vector              fPoints;
    protected LineDecoration      fStartDecoration = null;
    protected LineDecoration      fEndDecoration = null;
    protected Color               fFrameColor = Color.black;
    
    /*
     * Serialization support.
     */
    private static final long serialVersionUID = -7951352179906577773L;
    private int polyLineFigureSerializedDataVersion = 1;
    
    public PolyLineFigure() {
        fPoints = new Vector(4);
    }
    
    public PolyLineFigure(int size) {
        fPoints = new Vector(size);
    }
    
    public PolyLineFigure(int x, int y) {
	fPoints = new Vector();
	fPoints.addElement(new Point(x, y));
    }
    
    public Rectangle displayBox() {
        Enumeration k = points();
        Rectangle r = new Rectangle((Point) k.nextElement());
	
        while (k.hasMoreElements())
            r.add((Point) k.nextElement());
	
        return r;
    }
    
    public boolean isEmpty() {
        return (size().width < 3) && (size().height < 3);
    }
    
    public Vector handles() {
        Vector handles = new Vector(fPoints.size());
        for (int i = 0; i < fPoints.size(); i++)
            handles.addElement(new PolyLineHandle(this, locator(i), i));
        return handles;
    }
    
    public void basicDisplayBox(Point origin, Point corner) {
    }
    
    /**
     * Adds a node to the list of points.
     */
    public void addPoint(int x, int y) {
        fPoints.addElement(new Point(x, y));
        changed();
    }
    
    public Enumeration points() {
        return fPoints.elements();
    }
    
    public int pointCount() {
        return fPoints.size();
    }

    protected void basicMoveBy(int dx, int dy) {
        Enumeration k = fPoints.elements();
        while (k.hasMoreElements())
            ((Point) k.nextElement()).translate(dx, dy);
    }

    /**
     * Changes the position of a node.
     */
    public void setPointAt(Point p, int i) {
        willChange();
        fPoints.setElementAt(p, i);
        changed();
    }

    /**
     * Insert a node at the given point.
     */
    public void insertPointAt(Point p, int i) {
        fPoints.insertElementAt(p, i);
        changed();
    }

    public void removePointAt(int i) {
        willChange();
        fPoints.removeElementAt(i);
        changed();
    }

    /**
     * Splits the segment at the given point if a segment was hit.
     * @return the index of the segment or -1 if no segment was hit.
     */
    public int splitSegment(int x, int y) {
        int i = findSegment(x, y);
        if (i != -1)
            insertPointAt(new Point(x, y), i+1);
        return i+1;
    }

    public Point pointAt(int i) {
        return (Point)fPoints.elementAt(i);
    }

    /**
     * Joins to segments into one if the given point hits a node
     * of the polyline.
     * @return true if the two segments were joined.
     */
    public boolean joinSegments(int x, int y) {
        for (int i= 1; i < fPoints.size()-1; i++) {
            Point p = pointAt(i);
            if (Geom.length(x, y, p.x, p.y) < 3) {
                removePointAt(i);
                return true;
            }
        }
        return false;
    }

    public Connector connectorAt(int x, int y) {
        return new PolyLineConnector(this);
    }

    /**
     * Sets the start decoration.
     */
    public void setStartDecoration(LineDecoration l) {
        fStartDecoration = l;
    }

    /**
     * Sets the end decoration.
     */
    public void setEndDecoration(LineDecoration l) {
        fEndDecoration = l;
    }

    public void draw(Graphics g, boolean showGuides) {
        g.setColor(getFrameColor());
        Point p1, p2;
        for (int i = 0; i < fPoints.size()-1; i++) {
            p1 = (Point) fPoints.elementAt(i);
            p2 = (Point) fPoints.elementAt(i+1);
            g.drawLine(p1.x, p1.y, p2.x, p2.y);
        }
        decorate(g);
	if (showGuides) {
	    drawURL(g);
	}
    }

    private void drawURL(Graphics g) {
	String sensitive = (String)getAttribute("Sensitive");
	if (sensitive == null || sensitive.length() == 0)
	    return;
	int i;
	if (fPoints.size() < 3)
	    i = 0;
	else
	    i =  fPoints.size() / 2 - 1;
	Point p1, p2;

	if ((fPoints.size() & 1) == 1) {
	    p2 = p1 = (Point) fPoints.elementAt(i+1);
	} else {
	    p1 = (Point) fPoints.elementAt(i);
	    p2 = (Point) fPoints.elementAt(i+1);
	}
	g.setColor(Color.red);
	g.setFont(dialogFont);
	g.drawString("url=" + sensitive, (p1.x + p2.x) / 2,
		     (p1.y + p2.y) / 2);
    }

    public boolean containsPoint(int x, int y) {
        Rectangle bounds = displayBox();
        bounds.grow(4,4);
        if (!bounds.contains(x, y))
            return false;

        Point p1, p2;
        for (int i = 0; i < fPoints.size()-1; i++) {
            p1 = (Point) fPoints.elementAt(i);
            p2 = (Point) fPoints.elementAt(i+1);
            if (Geom.lineContainsPoint(p1.x, p1.y, p2.x, p2.y, x, y))
                return true;
        }
        return false;
    }

    /**
     * Gets the segment of the polyline that is hit by
     * the given point.
     * @return the index of the segment or -1 if no segment was hit.
     */
    public int findSegment(int x, int y) {
        Point p1, p2;
        for (int i = 0; i < fPoints.size()-1; i++) {
            p1 = (Point) fPoints.elementAt(i);
            p2 = (Point) fPoints.elementAt(i+1);
            if (Geom.lineContainsPoint(p1.x, p1.y, p2.x, p2.y, x, y))
                return i;
        }
        return -1;
    }

    private void decorate(Graphics g) {
        if (fStartDecoration != null) {
            Point p1 = (Point)fPoints.elementAt(0);
            Point p2 = (Point)fPoints.elementAt(1);
            fStartDecoration.draw(g, p1.x, p1.y, p2.x, p2.y);
        }
        if (fEndDecoration != null) {
            Point p3 = (Point)fPoints.elementAt(fPoints.size()-2);
            Point p4 = (Point)fPoints.elementAt(fPoints.size()-1);
            fEndDecoration.draw(g, p4.x, p4.y, p3.x, p3.y);
        }
    }

    /**
     * Gets the attribute with the given name.
     * PolyLineFigure maps "ArrowMode"to a
     * line decoration.
     */
    public Object getAttribute(String name) {
        if (name.equals("FrameColor")) {
            return getFrameColor();
        } else if (name.equals("ArrowMode")) {
            int value = 0;
            if (fStartDecoration != null)
                value |= ARROW_TIP_START;
            if (fEndDecoration != null)
                value |= ARROW_TIP_END;
            return new Integer(value);
	}
        return super.getAttribute(name);
    }

    /**
     * Sets the attribute with the given name.
     * PolyLineFigure interprets "ArrowMode"to set
     * the line decoration.
     */
    public void setAttribute(String name, Object value) {
        if (name.equals("FrameColor")) {
            setFrameColor((Color)value);
            changed();
        } else if (name.equals("ArrowMode")) {
            Integer intObj = (Integer) value;
            if (intObj != null) {
                int decoration = intObj.intValue();
                if ((decoration & ARROW_TIP_START) != 0)
                    fStartDecoration = new ArrowTip();
                else
                    fStartDecoration = null;
                if ((decoration & ARROW_TIP_END) != 0)
                    fEndDecoration = new ArrowTip();
                else
                    fEndDecoration = null;
            }
            changed();
	} else {
            super.setAttribute(name, value);
	    changed();
	}
    }

    public void write(StorableOutput dw) {
        super.write(dw);
        dw.writeInt(fPoints.size());
        Enumeration k = fPoints.elements();
        while (k.hasMoreElements()) {
            Point p = (Point) k.nextElement();
            dw.writeInt(p.x);
            dw.writeInt(p.y);
        }
        dw.writeStorable(fStartDecoration);
        dw.writeStorable(fEndDecoration);
        dw.writeColor(fFrameColor);
    }

    public String getMap() {
	String sensitive = (String)getAttribute("Sensitive");
	if (sensitive == null || sensitive.length() == 0)
	    return "";
	try {
		sensitive = URLDecoder.decode(sensitive);
	} catch (Exception e) {}
	Enumeration k = fPoints.elements();
	boolean first  = true;
	String forwards = "", backwards = "";
        for (int i = 1; i < fPoints.size(); i++) {
            Point p1 = (Point)fPoints.elementAt(i-1);
            Point p2 = (Point)fPoints.elementAt(i);
	    double l = Math.sqrt((p2.x-p1.x) * (p2.x-p1.x) +
				 (p2.y-p1.y) * (p2.y-p1.y));
	    int x = (int)(4 * (p2.y-p1.y) / l);
	    int y = (int)(4 * (p2.x-p1.x) / l);
	    if (!first) {
		forwards += ",";
		backwards = "," + backwards;
	    }
	    first = false;
	    forwards += (p1.x + x) + "," + (p1.y + y) + "," +
		(p2.x + x) + "," + (p2.y + y);
	    backwards = (p2.x - x) + "," + (p2.y - y) + "," +
		(p1.x - x) + "," + (p1.y - y) + backwards;
        }
	return "<area shape=\"poly\" coords=\"" +
	    forwards + "," + backwards + "\" href=\"" +
	    sensitive + "\" />\n";
    }

    public void read(StorableInput dr) throws IOException {
	// test for the next token being a number to allow us to
	// skip attribute reading which. Old-format files don't
	// have attributes on connections.
	super.read(dr);
        int size = dr.readInt();
	if (size == -1) {
	    // Temp for files created during devt. Remove when we're sure
	    // they are all gone
	    String s = dr.readString();
	    setAttribute("Sensitive", s);
	    size = dr.readInt();
	}
        fPoints = new Vector(size);
        for (int i=0; i<size; i++) {
            int x = dr.readInt();
            int y = dr.readInt();
            fPoints.addElement(new Point(x,y));
        }
        fStartDecoration = (LineDecoration)dr.readStorable();
        fEndDecoration = (LineDecoration)dr.readStorable();
        fFrameColor = dr.readColor();
    }

    /**
     * Creates a locator for the point with the given index.
     */
    public static Locator locator(int pointIndex) {
        return new PolyLineLocator(pointIndex);
    }

    protected Color getFrameColor() {
        return fFrameColor;
    }

    protected void setFrameColor(Color c) {
        fFrameColor = c;
    }
}

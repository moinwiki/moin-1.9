/*
 * @(#)EllipseFigure.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.io.*;
import java.net.*;
import java.util.Vector;
import CH.ifa.draw.util.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;

/**
 * An ellipse figure.
 */
public class EllipseFigure extends AttributeFigure {

    private Rectangle   fDisplayBox;

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = -6856203289355118951L;
    private int ellipseFigureSerializedDataVersion = 1;

    public EllipseFigure() {
        this(new Point(0,0), new Point(0,0));
    }

    public EllipseFigure(Point origin, Point corner) {
        basicDisplayBox(origin,corner);
    }

    public Vector handles() {
        Vector handles = new Vector();
        BoxHandleKit.addHandles(this, handles);
        return handles;
    }

    public void basicDisplayBox(Point origin, Point corner) {
        fDisplayBox = new Rectangle(origin);
        fDisplayBox.add(corner);
    }

    public Rectangle displayBox() {
        return new Rectangle(
            fDisplayBox.x,
            fDisplayBox.y,
            fDisplayBox.width,
            fDisplayBox.height);
    }

    protected void basicMoveBy(int x, int y) {
        fDisplayBox.translate(x,y);
    }

    public void drawBackground(Graphics g) {
        Rectangle r = displayBox();
        g.fillOval(r.x, r.y, r.width, r.height);
    }

    public void drawFrame(Graphics g) {
        Rectangle r = displayBox();
        g.drawOval(r.x, r.y, r.width-1, r.height-1);
    }

    public Insets connectionInsets() {
        Rectangle r = fDisplayBox;
        int cx = r.width/2;
        int cy = r.height/2;
        return new Insets(cy, cx, cy, cx);
    }

    public Connector connectorAt(int x, int y) {
        return new ChopEllipseConnector(this);
    }

    public void write(StorableOutput dw) {
        super.write(dw);
        dw.writeInt(fDisplayBox.x);
        dw.writeInt(fDisplayBox.y);
        dw.writeInt(fDisplayBox.width);
        dw.writeInt(fDisplayBox.height);
    }

    public String getMap() {
	String sense = (String)getAttribute("Sensitive");
	if (sense != null && sense.length() > 0) {
		try {
			sense = URLDecoder.decode(sense);
		} catch (Exception e) {}
	    Rectangle box = displayBox();
	    double w = box.width / 2.0;
	    double h = box.height / 2.0;
	    double ang = (box.height > box.width) ? Math.PI / 2 : 0;
	    Point c = center();
	    String coords = "";
	    for (int i = 0; i < 6; i++) {
		if (i > 0)
		    coords += ",";
		int x = (int)(c.x + Math.cos(ang) * w);
		int y = (int)(c.y + Math.sin(ang) * h);
		coords += x + "," + y;
		ang += Math.PI / 3;
	    }
	    return "<area shape=\"poly\" coords=\"" + coords +
		"\" href=\"" +
		sense + "\" />\n";
	}
	return "";
    }

    public void read(StorableInput dr) throws IOException {
        super.read(dr);
        fDisplayBox = new Rectangle(
            dr.readInt(),
            dr.readInt(),
            dr.readInt(),
            dr.readInt());
    }
}

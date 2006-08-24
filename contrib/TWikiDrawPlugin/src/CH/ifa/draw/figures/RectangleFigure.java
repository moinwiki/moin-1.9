/*
 * @(#)RectangleFigure.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.io.*;
import java.net.*;
import java.util.Vector;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.util.*;


/**
 * A rectangle figure.
 */
public class RectangleFigure extends AttributeFigure {

    private Rectangle   fDisplayBox;

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 184722075881789163L;
    private int rectangleFigureSerializedDataVersion = 1;

    public RectangleFigure() {
        this(new Point(0,0), new Point(0,0));
    }

    public RectangleFigure(Point origin, Point corner) {
        basicDisplayBox(origin,corner);
    }

    public void basicDisplayBox(Point origin, Point corner) {
        fDisplayBox = new Rectangle(origin);
        fDisplayBox.add(corner);
    }

    public Vector handles() {
        Vector handles = new Vector();
        BoxHandleKit.addHandles(this, handles);
        return handles;
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
	g.fillRect(r.x, r.y, r.width, r.height);
    }

    public void drawFrame(Graphics g) {
        Rectangle r = displayBox();
	g.drawRect(r.x, r.y, r.width-1, r.height-1);
    }

    //-- store / load ----------------------------------------------

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
	    return "<area shape=\"rect\" coords=\"" +
		box.x + "," + box.y + "," +
		(box.x + box.width) + "," +
		(box.y + box.height) +
		"\" href=\"" + sense + "\" />\n";
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

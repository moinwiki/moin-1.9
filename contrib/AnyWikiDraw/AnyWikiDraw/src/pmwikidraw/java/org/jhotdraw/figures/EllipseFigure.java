/*
 * @(#)EllipseFigure.java
 *
 * Project:		JHotdraw - a GUI framework for technical drawings
 *				http://www.jhotdraw.org
 *				http://jhotdraw.sourceforge.net
 * Copyright:	© by the original author(s) and all contributors
 * License:		Lesser GNU Public License (LGPL)
 *				http://www.opensource.org/licenses/lgpl-license.html
 */

package org.jhotdraw.figures;

import java.awt.Graphics;
import java.awt.Insets;
import java.awt.Point;
import java.awt.Rectangle;
import java.io.IOException;
import java.util.List;

import org.jhotdraw.framework.Connector;
import org.jhotdraw.framework.FigureAttributeConstant;
import org.jhotdraw.framework.HandleEnumeration;
import org.jhotdraw.standard.BoxHandleKit;
import org.jhotdraw.standard.HandleEnumerator;
import org.jhotdraw.util.CollectionsFactory;
import org.jhotdraw.util.StorableInput;
import org.jhotdraw.util.StorableOutput;

import com.wombatinvasion.pmwikidraw.PmWikiDrawURLEncoder;

/**
 * An ellipse figure.
 *
 * @version <$CURRENT_VERSION$>
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

	public HandleEnumeration handles() {
		List handles = CollectionsFactory.current().createList();
		BoxHandleKit.addHandles(this, handles);
		return new HandleEnumerator(handles);
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
        /*
         * JP, 25-May-03: Changed from (width-1, height-1) to (width, height),
         * because figures were not filled completely (JDK 1.4.x). Might invalidate
         * fix for #661878. If the problem is JDK-dependant, maybe the JDK version
         * should be taken into account here?
         */
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

	public void read(StorableInput dr) throws IOException {
		super.read(dr);
		fDisplayBox = new Rectangle(
			dr.readInt(),
			dr.readInt(),
			dr.readInt(),
			dr.readInt());
	}
	
	/* Added by CJ 13/11/04 */
	public String getMap() {
    	String sense = (String)getAttribute(FigureAttributeConstant.URL);
    	if (sense != null && sense.length() > 0) {
    	    try {
    	    	sense = PmWikiDrawURLEncoder.decode(sense);
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
    		"\" href=\"" + sense + "\" alt=\"" + sense + "\" />";
    	}
    	return "";
    }	
}

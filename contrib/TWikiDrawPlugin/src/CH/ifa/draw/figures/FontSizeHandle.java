/*
 * @(#)FontSizeHandle.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;

/**
 * A Handle to change the font size by direct manipulation.
 */
public class FontSizeHandle extends LocatorHandle {

    private Font    fFont;
    private int     fSize;

    public FontSizeHandle(Figure owner, Locator l) {
        super(owner, l);
    }

    public void invokeStart(int  x, int  y, DrawingView view) {
        TextFigure textOwner = (TextFigure) owner();
        fFont = textOwner.getFont();
        fSize = fFont.getSize();
    }

    public void invokeStep (int x, int y, int anchorX, int anchorY, DrawingView view) {
        TextFigure textOwner = (TextFigure) owner();
        int newSize = fSize + y-anchorY;
        textOwner.setFont(new Font(fFont.getName(), fFont.getStyle(), newSize) );
    }

    public void draw(Graphics g) {
        Rectangle r = displayBox();

        g.setColor(Color.yellow);
        g.fillOval(r.x, r.y, r.width, r.height);

        g.setColor(Color.black);
        g.drawOval(r.x, r.y, r.width, r.height);
    }
}

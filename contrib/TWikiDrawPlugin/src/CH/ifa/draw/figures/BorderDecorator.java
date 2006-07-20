/*
 * @(#)BorderDecorator.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.util.*;

import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;

/**
 * BorderDecorator decorates an arbitrary Figure with
 * a border.
 */
public  class BorderDecorator extends DecoratorFigure {

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 1205601808259084917L;
    private int borderDecoratorSerializedDataVersion = 1;

    public BorderDecorator() { }
    public BorderDecorator(Figure figure) {
        super(figure);
    }

    private Point border() {
        return new Point(3,3);
    }

    /**
     * Draws a the figure and decorates it with a border.
     */
    public void draw(Graphics g, boolean showGuides) {
        Rectangle r = displayBox();
        super.draw(g, showGuides);
        g.setColor(Color.white);
        g.drawLine(r.x, r.y, r.x, r.y + r.height);
        g.drawLine(r.x, r.y, r.x + r.width, r.y);
        g.setColor(Color.gray);
        g.drawLine(r.x + r.width, r.y, r.x + r.width, r.y + r.height);
        g.drawLine(r.x , r.y + r.height, r.x + r.width, r.y + r.height);
    }

    /**
     * Gets the displaybox including the border.
     */
    public Rectangle displayBox() {
        Rectangle r = fComponent.displayBox();
        r.grow(border().x, border().y);
        return r;
    }

    /**
     * Invalidates the figure extended by its border.
     */
    public void figureInvalidated(FigureChangeEvent e) {
        Rectangle rect = e.getInvalidatedRectangle();
        rect.grow(border().x, border().y);
        super.figureInvalidated(new FigureChangeEvent(e.getFigure(), rect));
    }

    public Insets connectionInsets() {
        Insets i = super.connectionInsets();
        i.top -= 3;
        i.bottom -= 3;
        i.left -= 3;
        i.right -= 3;
        return i;
    }
}

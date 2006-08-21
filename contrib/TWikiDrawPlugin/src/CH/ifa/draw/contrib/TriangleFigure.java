/*
 * Hacked together by Doug lea
 * Tue Feb 25 17:30:58 1997  Doug Lea  (dl at gee)
 *
 */

package CH.ifa.draw.contrib;

import java.awt.*;
import java.util.*;
import java.io.IOException;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.util.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.figures.*;

/**
 * A triangle with same dimensions as its enclosing rectangle,
 * and apex at any of 8 places
 */
public  class TriangleFigure extends RectangleFigure {

  static double[] rotations = {
    -Math.PI/2, -Math.PI/4,
    0.0, Math.PI/4,
    Math.PI/2, Math.PI * 3/4,
    Math.PI,  -Math.PI * 3/4
  };

  protected int fRotation = 0;

  public TriangleFigure() {
    super(new Point(0,0), new Point(0,0));
  }

  public TriangleFigure(Point origin, Point corner) {
    super(origin, corner);
  }

  public Vector handles() {
    Vector h = super.handles();
    h.addElement(new TriangleRotationHandle(this));
    return h;
  }

  public void rotate(double angle) {
    willChange();
    //System.out.println("a:"+angle);
    double dist = Double.MAX_VALUE;
    int best = 0;
    for (int i = 0; i < rotations.length; ++i) {
      double d = Math.abs(angle - rotations[i]);
      if (d < dist) {
        dist = d;
        best = i;
      }
    }
    fRotation = best;
    changed();
  }

  /** Return the polygon describing the triangle **/
  public Polygon polygon() {
    Rectangle r = displayBox();
    Polygon p = new Polygon();
    switch (fRotation) {
    case 0:
      p.addPoint(r.x+r.width/2, r.y);
      p.addPoint(r.x+r.width, r.y+r.height);
      p.addPoint(r.x, r.y+r.height);
      break;
    case 1:
      p.addPoint(r.x + r.width, r.y);
      p.addPoint(r.x+r.width, r.y+r.height);
      p.addPoint(r.x, r.y);
      break;
    case 2:
      p.addPoint(r.x + r.width, r.y+r.height/2);
      p.addPoint(r.x, r.y+r.height);
      p.addPoint(r.x, r.y);
      break;
    case 3:
      p.addPoint(r.x+r.width, r.y+r.height);
      p.addPoint(r.x, r.y+r.height);
      p.addPoint(r.x + r.width, r.y);
      break;
    case 4:
      p.addPoint(r.x+r.width/2, r.y+r.height);
      p.addPoint(r.x, r.y);
      p.addPoint(r.x + r.width, r.y);
      break;
    case 5:
      p.addPoint(r.x, r.y+r.height);
      p.addPoint(r.x, r.y);
      p.addPoint(r.x+r.width, r.y+r.height);
      break;
    case 6:
      p.addPoint(r.x, r.y+r.height/2);
      p.addPoint(r.x + r.width, r.y);
      p.addPoint(r.x+r.width, r.y+r.height);
      break;
    case 7:
      p.addPoint(r.x, r.y);
      p.addPoint(r.x + r.width, r.y);
      p.addPoint(r.x, r.y+r.height);
      break;
    }
    return p;
  }


  public void draw(Graphics g) {
    Polygon p = polygon();
    g.setColor(getFillColor());
    g.fillPolygon(p);
    g.setColor(getFrameColor());
    g.drawPolygon(p);
  }


  public Insets connectionInsets() {
    Rectangle r = displayBox();
    switch(fRotation) {
    case 0:
      return new Insets(r.height, r.width/2, 0, r.width/2);
    case 1:
      return new Insets(0, r.width, r.height, 0);
    case 2:
      return new Insets(r.height/2, 0, r.height/2, r.width);
    case 3:
      return new Insets(r.height, r.width, 0, 0);
    case 4:
      return new Insets(0, r.width/2, r.height, r.width/2);
    case 5:
      return new Insets(r.height, 0, 0, r.width);
    case 6:
      return new Insets(r.height/2, r.width, r.height/2, 0);
    case 7:
      return new Insets(0, 0, r.height, r.width);
    default:
      return null;
    }
  }

  public boolean containsPoint(int x, int y) {
    return polygon().contains(x, y);
  }

  public Point center() {
    return PolygonFigure.center(polygon());
  }

  public Point chop(Point p) {
    return PolygonFigure.chop(polygon(), p);
  }

  public Object clone() {
    TriangleFigure figure = (TriangleFigure) super.clone();
    figure.fRotation = fRotation;
    return figure;
  }

    //-- store / load ----------------------------------------------

    public void write(StorableOutput dw) {
      super.write(dw);
      dw.writeInt(fRotation);
    }

    public void read(StorableInput dr) throws IOException {
      super.read(dr);
      fRotation = dr.readInt();
    }
}

/*
 * @(#)ImageFigure.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.awt.*;
import java.io.*;
import java.util.Vector;
import java.awt.image.ImageObserver;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.util.*;

/**
 * A Figure that shows an Image.
 * Images shown by an image figure are shared by using the Iconkit.
 * @see Iconkit
 */
public  class ImageFigure
        extends AttributeFigure implements ImageObserver {

    private String   fFileName;
    private transient Image fImage;
    private Rectangle fDisplayBox;
    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 148012030121282439L;
    private int imageFigureSerializedDataVersion = 1;

    public ImageFigure() {
        fFileName = null;
        fImage = null;
        fDisplayBox = null;
    }

    public ImageFigure(Image image, String fileName, Point origin) {
        fFileName = fileName;
        fImage = image;
        fDisplayBox = new Rectangle(origin.x, origin.y, 0, 0);
        fDisplayBox.width = fImage.getWidth(this);
        fDisplayBox.height = fImage.getHeight(this);
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

    public void draw(Graphics g) {
        if (fImage == null)
            fImage = Iconkit.instance().getImage(fFileName);
        if (fImage != null)
            g.drawImage(fImage, fDisplayBox.x, fDisplayBox.y, fDisplayBox.width, fDisplayBox.height, this);
        else
            drawGhost(g);
    }

    private void drawGhost(Graphics g) {
        g.setColor(Color.gray);
        g.fillRect(fDisplayBox.x, fDisplayBox.y, fDisplayBox.width, fDisplayBox.height);
    }

   /**
    * Handles asynchroneous image updates.
    */
    public boolean imageUpdate(Image img, int flags, int x, int y, int w, int h) {
	    if ((flags & (FRAMEBITS|ALLBITS)) != 0) {
	        invalidate();
	        if (listener() != null)
	            listener().figureRequestUpdate(new FigureChangeEvent(this));
	    }
	    return (flags & (ALLBITS|ABORT)) == 0;
    }

   /**
    * Writes the ImageFigure to a StorableOutput. Only a reference to the
    * image, that is its pathname is saved.
    */
    public void write(StorableOutput dw) {
        super.write(dw);
        dw.writeInt(fDisplayBox.x);
        dw.writeInt(fDisplayBox.y);
        dw.writeInt(fDisplayBox.width);
        dw.writeInt(fDisplayBox.height);
        dw.writeString(fFileName);
    }

   /**
    * Reads the ImageFigure from a StorableInput. It registers the
    * referenced figure to be loaded from the Iconkit.
    * @see Iconkit#registerImage
    */
    public void read(StorableInput dr) throws IOException {
        super.read(dr);
        fDisplayBox = new Rectangle(
            dr.readInt(),
            dr.readInt(),
            dr.readInt(),
            dr.readInt());
        fFileName = dr.readString();
        Iconkit.instance().registerImage(fFileName);
    }

    private void readObject(ObjectInputStream s)
        throws ClassNotFoundException, IOException {

        s.defaultReadObject();
        Iconkit.instance().registerImage(fFileName);
        fImage = null;
    }
}

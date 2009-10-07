/*
 * @(#)TextFigure.java 5.1
 *
 */

package CH.ifa.draw.figures;

import java.util.*;
import java.awt.*;
import java.io.*;
import CH.ifa.draw.framework.*;
import CH.ifa.draw.standard.*;
import CH.ifa.draw.util.*;

/**
 * A text figure.
 *
 * @see TextTool
 */
public  class TextFigure
        extends AttributeFigure
        implements FigureChangeListener, TextHolder {

    private int               fOriginX;
    private int               fOriginY;

    // cache of the TextFigure's size
    transient private boolean fSizeIsDirty = true;
    transient private int     fWidth;
    transient private int     fHeight;

    private String  fText;
    private Font    fFont;
    private boolean fIsReadOnly;
    private int  fAlign;

    private static final int TEXTALIGN_LEFT = 0;
    private static final int TEXTALIGN_CENTRE = 1;
    private static final int TEXTALIGN_RIGHT = 2;

    private Figure  fObservedFigure = null;
    private OffsetLocator fLocator = null;

    private static String fgCurrentFontName  = "Helvetica";
    private static int    fgCurrentFontSize  = 12;
    private static int    fgCurrentFontStyle = Font.PLAIN;

    /*
     * Serialization support.
     */
    private static final long serialVersionUID = 4599820785949456124L;
    private int textFigureSerializedDataVersion = 1;

    public TextFigure() {
        fOriginX = 0;
        fOriginY = 0;
        fFont = createCurrentFont();
        setAttribute("FillColor", ColorMap.getColorMap().color("None"));
	fAlign = TEXTALIGN_LEFT;
        fText = new String("");
        fSizeIsDirty = true;
    }

    public void moveBy(int x, int y) {
        willChange();
        basicMoveBy(x, y);
        if (fLocator != null)
            fLocator.moveBy(x, y);
        changed();
    }

    protected void basicMoveBy(int x, int y) {
        fOriginX += x;
        fOriginY += y;
    }

    public void basicDisplayBox(Point newOrigin, Point newCorner) {
        fOriginX = newOrigin.x;
        fOriginY = newOrigin.y;
    }

    public Rectangle displayBox() {
        Dimension extent = textExtent();
        return new Rectangle(fOriginX, fOriginY, extent.width, extent.height);
    }

    public Rectangle textDisplayBox() {
        return displayBox();
    }

    /**
     * Tests whether this figure is read only.
     */
    public boolean readOnly() {
        return fIsReadOnly;
    }

    /**
     * Sets the read only status of the text figure.
     */
    public void setReadOnly(boolean isReadOnly) {
        fIsReadOnly = isReadOnly;
    }

    /**
     * Gets the font.
     */
    public Font getFont() {
        return fFont;
    }

    /**
     * Sets the font.
     */
    public void setFont(Font newFont) {
        willChange();
        fFont = newFont;
        markDirty();
        changed();
    }

    /**
     * Updates the location whenever the figure changes itself.
     */
    public void changed() {
        super.changed();
        updateLocation();
    }

    /**
     * A text figure understands the "FontSize", "FontStyle", "FontName"
     * and "TextAlign" attributes.
     */
    public Object getAttribute(String name) {
        Font font = getFont();
        if (name.equals("FontSize"))
            return new Integer(font.getSize());
        if (name.equals("FontStyle"))
            return new Integer(font.getStyle());
        if (name.equals("FontName"))
            return font.getName();
	if (name.equals("TextAlign")) {
	    switch (fAlign) {
	    default: return "Left";
	    case TEXTALIGN_CENTRE: return "Centre";
	    case TEXTALIGN_RIGHT: return "Right";
	    }
	}
        return super.getAttribute(name);
    }

    /**
     * A text figure understands the "FontSize", "FontStyle", "FontName"
     * and "Align" attributes.
     */
    public void setAttribute(String name, Object value) {
        Font font = getFont();
        if (name.equals("FontSize")) {
            Integer s = (Integer)value;
            setFont(new Font(font.getName(), font.getStyle(), s.intValue()) );
        }
        else if (name.equals("FontStyle")) {
            Integer s = (Integer)value;
            int style = font.getStyle();
            if (s.intValue() == Font.PLAIN)
                style = font.PLAIN;
            else
                style = style ^ s.intValue();
            setFont(new Font(font.getName(), style, font.getSize()) );
        }
        else if (name.equals("FontName")) {
            String n = (String)value;
            setFont(new Font(n, font.getStyle(), font.getSize()) );
        }
	else if (name.equals("TextAlign")) {
            String n = (String)value;
	    if (n.equals("Centre"))
		fAlign = TEXTALIGN_CENTRE;
	    else if (n.equals("Right"))
		fAlign = TEXTALIGN_RIGHT;
	    else
		fAlign = TEXTALIGN_LEFT;
            changed();
	}
        else
            super.setAttribute(name, value);
    }

    /**
     * Gets the text shown by the text figure.
     */
    public String getText() {
        return fText;
    }

    /**
     * Sets the text shown by the text figure.
     */
    public void setText(String newText) {
        if (!newText.equals(fText)) {
            willChange();
            fText = new String(newText);
            markDirty();
            changed();
        }
    }

    /**
     * Tests whether the figure accepts typing.
     */
    public boolean acceptsTyping() {
        return !fIsReadOnly;
    }

    public void drawBackground(Graphics g) {
        Rectangle r = displayBox();
        g.fillRect(r.x, r.y, r.width, r.height);
    }

    public void drawFrame(Graphics g) {
        g.setFont(fFont);
        g.setColor((Color) getAttribute("TextColor"));
        FontMetrics metrics = g.getFontMetrics(fFont);
	StringTokenizer st = new StringTokenizer(fText, "\n");
	Dimension d = textExtent();
	
	int orgy = fOriginY;
	while (st.hasMoreTokens()) {
	    String t = st.nextToken();
	    int xpos = fOriginX;
	    if (fAlign == TEXTALIGN_RIGHT) {
		xpos += d.width - metrics.stringWidth(t);
	    } else if (fAlign == TEXTALIGN_CENTRE) {
		xpos += (d.width - metrics.stringWidth(t)) / 2;
	    }
	    g.drawString(t, xpos, orgy + metrics.getAscent());
	    orgy += metrics.getHeight();
	}
    }

    private Dimension textExtent() {
        if (!fSizeIsDirty)
            return new Dimension(fWidth, fHeight);
        FontMetrics metrics =
	    Toolkit.getDefaultToolkit().getFontMetrics(fFont);
	fWidth = 0;
	fHeight = 0;
	StringTokenizer st = new StringTokenizer(fText, "\n");
	while (st.hasMoreTokens()) {
	    String t = st.nextToken();
	    fHeight += metrics.getHeight();
	    int w = metrics.stringWidth(t);
	    if (w > fWidth)
		fWidth = w;
	}

        fSizeIsDirty = false;
        return new Dimension(fWidth, fHeight);
    }

    private void markDirty() {
        fSizeIsDirty = true;
    }

    private Dimension getRowsAndColumns(String text) {
	int rows = 0;
	int cols = 0;
	StringTokenizer st = new StringTokenizer(fText, "\n");
	while (st.hasMoreTokens()) {
	    String t = st.nextToken();
	    if (t.length() > cols)
		cols = t.length();
	    rows++;
	}
	return new Dimension(cols, rows);
    }

    /**
     * Gets the number of columns to be overlaid when the figure is edited.
     */
    public int overlayColumns() {
	Dimension d = getRowsAndColumns(getText());
        return d.width < 20 ? 20 : d.width;
    }

    /**
     * Gets the number of rows to be overlaid when the figure is edited.
     */
    public int overlayRows() {
	Dimension d = getRowsAndColumns(getText());
        return d.height < 5 ? 5 : d.height;
    }

    public Vector handles() {
        Vector handles = new Vector();
        handles.addElement(new NullHandle(this, RelativeLocator.northWest()));
        handles.addElement(new NullHandle(this, RelativeLocator.northEast()));
        handles.addElement(new NullHandle(this, RelativeLocator.southEast()));
        handles.addElement(new FontSizeHandle(this, RelativeLocator.southWest()));
        return handles;
    }

    public void write(StorableOutput dw) {
        super.write(dw);
        dw.writeInt(fOriginX);
        dw.writeInt(fOriginY);
        dw.writeString(fText);
        dw.writeString(fFont.getName());
        dw.writeInt(fFont.getStyle());
        dw.writeInt(fFont.getSize());
        dw.writeBoolean(fIsReadOnly);
        dw.writeStorable(fObservedFigure);
        dw.writeStorable(fLocator);
    }

    public void read(StorableInput dr) throws IOException {
        super.read(dr);
        markDirty();
        fOriginX = dr.readInt();
        fOriginY = dr.readInt();
        fText = dr.readString();
        fFont = new Font(dr.readString(), dr.readInt(), dr.readInt());
        fIsReadOnly = dr.readBoolean();

        fObservedFigure = (Figure)dr.readStorable();
        if (fObservedFigure != null) {
            setAttribute("observed.figure", fObservedFigure);
            fObservedFigure.addFigureChangeListener(this);
        }
        fLocator = (OffsetLocator)dr.readStorable();
    }

    private void readObject(ObjectInputStream s)
        throws ClassNotFoundException, IOException {

        s.defaultReadObject();

        if (fObservedFigure != null)
            fObservedFigure.addFigureChangeListener(this);
        markDirty();
    }

    public void connect(Figure figure) {
        if (fObservedFigure != null)
            fObservedFigure.removeFigureChangeListener(this);

        fObservedFigure = figure;
        fLocator = new OffsetLocator(figure.connectedTextLocator(this));
        fObservedFigure.addFigureChangeListener(this);
        setAttribute("observed.figure", fObservedFigure);
        updateLocation();
    }

    public void figureChanged(FigureChangeEvent e) {
        updateLocation();
    }

    public void figureRemoved(FigureChangeEvent e) {
        if (listener() != null)
            listener().figureRequestRemove(new FigureChangeEvent(this));
    }

    public void figureRequestRemove(FigureChangeEvent e) {}
    public void figureInvalidated(FigureChangeEvent e) {}
    public void figureRequestUpdate(FigureChangeEvent e) {}

    /**
     * Updates the location relative to the connected figure.
     * The TextFigure is centered around the located point.
     */
    protected void updateLocation() {
        if (fLocator != null) {
            Point p = fLocator.locate(fObservedFigure);
            p.x -= size().width/2 + fOriginX;
            p.y -= size().height/2 + fOriginY;

            if (p.x != 0 || p.y != 0) {
                willChange();
                basicMoveBy(p.x, p.y);
                changed();
            }
        }
    }

    public void release() {
        super.release();
        if (fObservedFigure != null)
            fObservedFigure.removeFigureChangeListener(this);
    }

    /**
     * Disconnects the text figure.
     */
    public void disconnect() {
        fObservedFigure.removeFigureChangeListener(this);
        fObservedFigure = null;
        fLocator = null;
        setAttribute("observed.figure", null);
    }


    /**
     * Creates the current font to be used for new text figures.
     */
    static public Font createCurrentFont() {
        return new Font(fgCurrentFontName, fgCurrentFontStyle, fgCurrentFontSize);
    }

    /**
     * Sets the current font name
     */
    static public void setCurrentFontName(String name) {
        fgCurrentFontName = name;
    }

    /**
     * Sets the current font size.
     */
    static public void setCurrentFontSize(int size) {
        fgCurrentFontSize = size;
    }

    /**
     * Sets the current font style.
     */
    static public void setCurrentFontStyle(int style) {
        fgCurrentFontStyle = style;
    }
}

/*
 * @(#)PaletteButton.java 5.1
 *
 */

package CH.ifa.draw.util;

import java.awt.*;
import java.awt.event.*;

/**
 * A palette button is a three state button. The states are normal
 * pressed and selected. It uses to the palette listener interface
 * to notify about state changes.
 *
 * @see PaletteListener
 * @see PaletteLayout
*/

public abstract class PaletteButton
                extends Canvas
                implements MouseListener, MouseMotionListener {

    static final int NORMAL = 1;
    static final int PRESSED = 2;
    static final int SELECTED = 3;

    private PaletteListener  fListener;
    private int             fState;
    private int             fOldState;


    /**
     * Constructs a PaletteButton.
     * @param listener the listener to be notified.
     */
    public PaletteButton(PaletteListener listener) {
        fListener = listener;
        fState = fOldState = NORMAL;
        addMouseListener(this);
        addMouseMotionListener(this);
    }

    public abstract void paintBackground(Graphics g);
    public abstract void paintNormal(Graphics g);
    public abstract void paintPressed(Graphics g);
    public abstract void paintSelected(Graphics g);

    public Object value() {
        return null;
    }

    public String name() {
        return "";
    }

    public void reset() {
        fState = NORMAL;
        repaint();
    }

    public void select() {
        fState = SELECTED;
        repaint();
    }

    public void mousePressed(MouseEvent e) {
        fOldState = fState;
        fState = PRESSED;
        repaint();
    }

    public void mouseDragged(MouseEvent e) {
        if (contains(e.getX(),e.getY()))
            fState = PRESSED;
        else
            fState = fOldState;
        repaint();
    }

    public void mouseReleased(MouseEvent e) {
        fState = fOldState;
        repaint();
        if (contains(e.getX(),e.getY()))
            fListener.paletteUserSelected(this);
    }

    public void mouseMoved(MouseEvent e) {
        fListener.paletteUserOver(this, true);
    }

    public void mouseExited(MouseEvent e) {
        if (fState == PRESSED) // JDK1.1 on Windows sometimes looses mouse released
            mouseDragged(e);
        fListener.paletteUserOver(this, false);
    }

    public void mouseClicked(MouseEvent e) {}
    public void mouseEntered(MouseEvent e) {}

    public void update(Graphics g) {
        paint(g);
    }

    public void paint(Graphics g) {
        paintBackground(g);

        switch (fState) {
        case PRESSED:
            paintPressed(g);
            break;
        case SELECTED:
            paintSelected(g);
            break;
        case NORMAL:
        default:
            paintNormal(g);
            break;
        }
    }
}

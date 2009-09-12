/**
 * @(#)JHarmonicColorWheel.java
 *
 * Copyright (c) 2008 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and
 * contributors of the JHotDraw project ("the copyright holders").
 * You may not use, copy or modify this software, except in
 * accordance with the license agreement you entered into with
 * the copyright holders. For details see accompanying license terms.
 */
package org.jhotdraw.color;

import java.awt.*;
import java.awt.event.*;
import java.awt.geom.*;
import java.beans.*;
import javax.swing.event.*;

/**
 * JHarmonicColorWheel.
 * 
 * FIXME - This is an experimental class. Do not use it.
 *
 * @author Werner Randelshofer
 * @version $Id: JHarmonicColorWheel.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class JHarmonicColorWheel extends JColorWheel {

    public final static String SELECTED_INDEX_PROPERTY = "selectedIndex";
    private HarmonicColorModel harmonicModel;
    private int selectedIndex = -1;
    private float handleRadius = 4f;
    private float baseRadius = 7f;

    private class MouseHandler implements MouseListener, MouseMotionListener {

        public void mouseClicked(MouseEvent e) {
        }

        public void mouseDragged(MouseEvent e) {
            update(e);
        }

        public void mouseEntered(MouseEvent e) {
        }

        public void mouseExited(MouseEvent e) {
        }

        public void mouseMoved(MouseEvent e) {
        }

        public void mousePressed(MouseEvent e) {
            int x = e.getX();
            int y = e.getY();
            int closestIndex = -1;
            if (harmonicModel != null && harmonicModel.size() > 0) {
                int closestError = Integer.MAX_VALUE;
                for (int i = 0, n = harmonicModel.size(); i < n; i++) {
                    CompositeColor c = harmonicModel.get(i);
                    if (c != null) {
                        Point p = getColorLocation(harmonicModel.get(i));
                        int error = (p.x - x) * (p.x - x) +
                                (p.y - y) * (p.y - y);
                        if (error < closestError) {
                            closestIndex = i;
                            closestError = error;
                        }
                    }
                }
                if (closestIndex != -1) {
                    if (closestError > 20) {
                        closestIndex = -1;
                    }
                }
            }
            setSelectedIndex(closestIndex);
        }

        public void mouseReleased(MouseEvent e) {
            //update(e);
        }

        private void update(MouseEvent e) {
            if (selectedIndex != -1) {
                float[] hsb = getColorAt(e.getX(), e.getY());
                hsb[1] = harmonicModel.get(selectedIndex).getComponent(1);
                //if (hsb != null) {
                harmonicModel.set(selectedIndex, new CompositeColor(harmonicModel.getColorSystem(), hsb));
                //}
                repaint();
            }
        }
    }
    private MouseHandler mouseHandler;

    private class ModelHandler implements PropertyChangeListener, ListDataListener {

        public void propertyChange(PropertyChangeEvent evt) {
            String name = evt.getPropertyName();
            if (name == HarmonicColorModel.COLOR_SYSTEM_PROPERTY) {
                model.setColorSystem(harmonicModel.getColorSystem());
                model.setComponentValue(1, 1f);
                colorWheelProducer = createWheelProducer(getWidth(), getHeight());
                colorWheelImage = null;
            }
            repaint();
        }

        public void intervalAdded(ListDataEvent e) {
            repaint();
        }

        public void intervalRemoved(ListDataEvent e) {
            repaint();
        }

        public void contentsChanged(ListDataEvent e) {
            repaint();
        }
    }
    private ModelHandler modelHandler;

    /** Creates new form. */
    public JHarmonicColorWheel() {
        super(new HSLRYBColorSystem());
        initComponents();

        setRadialComponentIndex(2);
        setVerticalComponentIndex(1);
        getModel().setComponentValue(1, 1f);
        setWheelInsets(new Insets(5, 5, 5, 5));

        modelHandler = new ModelHandler();

        DefaultHarmonicColorModel p = new DefaultHarmonicColorModel();
        setHarmonicColorModel(p);
        setToolTipText("");

    }

    public void setColorSystem(ColorSystem newValue) {
        harmonicModel.setColorSystem(newValue);
        getModel().setColorSystem(newValue);
        getModel().setComponentValue(1, 1f);
    }

    public HarmonicColorModel getHarmonicColorModel() {
        return harmonicModel;
    }

    public String getToolTipText(MouseEvent evt) {
        float[] hsb = getColorAt(evt.getX(), evt.getY());
        if (hsb == null) {
            return null;
        }

        StringBuilder buf = new StringBuilder();

        buf.append(Math.round(hsb[0] * 360));
        buf.append(",");
        buf.append(Math.round(hsb[1] * 100f));
        buf.append(",");
        buf.append(Math.round(hsb[2] * 100f));

        if (buf.length() > 0) {
            buf.insert(0, "<html>");

            return buf.toString();
        } else {
            return null;
        }
    }

    @Override
    protected void installMouseListeners() {
        mouseHandler = new MouseHandler();
        addMouseListener(mouseHandler);
        addMouseMotionListener(mouseHandler);
    }

    public void setHarmonicColorModel(HarmonicColorModel newValue) {
        HarmonicColorModel oldValue = harmonicModel;
        if (oldValue != null) {
            oldValue.removePropertyChangeListener(modelHandler);
            oldValue.removeListDataListener(modelHandler);
        }
        harmonicModel = newValue;
        if (newValue != null) {
            newValue.addPropertyChangeListener(modelHandler);
            newValue.addListDataListener(modelHandler);
            colorWheelProducer = createWheelProducer(getWidth(), getHeight());
        }
    }
    /*
    @Override
    protected ColorWheelImageProducer createWheelProducer(int w, int h) {
    return new HSLHarmonicColorWheelImageProducer(harmonicModel == null ? new HSLRYBColorSystem() : harmonicModel.getColorSystem(), w, h);
    }*/

    @Override
    public void paintComponent(Graphics gr) {
        Graphics2D g = (Graphics2D) gr;
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE);
        super.paintComponent(g);
    }

    @Override
    protected void paintThumb(Graphics2D g) {
        paintTicks(g);

        if (harmonicModel != null) {
            Point center = getCenter();
            Ellipse2D.Float oval = new Ellipse2D.Float(0, 0, 0, 0);

            float[] comp = null;
            float wheelBrightness = model.getBoundedRangeModel(2).getValue() / 100f;
            for (int i = harmonicModel.size() - 1; i >= 0; i--) {
                if (harmonicModel.get(i) != null) {
                    Point p = getColorLocation(harmonicModel.get(i));
                    g.setColor(Color.black);
                    g.drawLine(center.x, center.y, p.x, p.y);
                }
            }
            for (int i = harmonicModel.size() - 1; i >= 0; i--) {
                if (harmonicModel.get(i) != null) {
                    Point p = getColorLocation(harmonicModel.get(i));
                    CompositeColor mixerColor = harmonicModel.get(i);
                    comp = mixerColor.getComponents();
                    if (i == selectedIndex) {
                        g.setColor(Color.white);
                        oval.x = p.x - baseRadius;
                        oval.y = p.y - baseRadius;
                        oval.width = baseRadius * 2f;
                        oval.height = baseRadius * 2f;
                        g.fill(oval);
                    }
                    g.setColor(mixerColor.getColor());
                    oval.x = p.x - handleRadius;
                    oval.y = p.y - handleRadius;
                    oval.width = handleRadius * 2f;
                    oval.height = handleRadius * 2f;
                    g.fill(oval);
                    g.setColor(Color.black);
                    g.draw(oval);
                    if (i == harmonicModel.getBase()) {
                        oval.x = p.x - baseRadius;
                        oval.y = p.y - baseRadius;
                        oval.width = baseRadius * 2f;
                        oval.height = baseRadius * 2f;
                        g.draw(oval);
                    }
                // g.drawString(i+"", p.x, p.y);
                }
            }
        }
    }

    protected void paintTicks(Graphics2D g) {
        if (true) return;
        if (harmonicModel != null) {
            Point center = getCenter();
            float radius = getRadius();
            Ellipse2D.Float oval = new Ellipse2D.Float(0, 0, 0, 0);

            int baseIndex = harmonicModel.getBase();
            CompositeColor bc = harmonicModel.get(baseIndex);
            g.setColor(Color.DARK_GRAY);
            
            for (int i = 0; i < 12; i++) {
                float angle = bc.getComponent(0) + i / 12f;

                float radial1 = radius;
                /*g.draw(new Line2D.Double(
                        center.x + radius * Math.cos(angle * Math.PI * 2d),
                        center.y - radius * Math.sin(angle * Math.PI * 2d),
                        center.x + (radius + 2) * Math.cos(angle * Math.PI * 2d),
                        center.y - (radius + 2) * Math.sin(angle * Math.PI * 2d)));
               */
                g.fill(new Ellipse2D.Double(
                        center.x + (radius+2) * Math.cos(angle * Math.PI * 2d)-2,
                        center.y - (radius+2) * Math.sin(angle * Math.PI * 2d)-2,
                        4,
                        4));

            }

            for (int i = 0, n = harmonicModel.size(); i < n; i++) {
                if (i != baseIndex) {
                    CompositeColor dc = harmonicModel.get(i);
                    if (dc != null) {
                        float angle = dc.getComponent(0);

                        float diff = Math.abs(angle - bc.getComponent(0)) * 12;
                        if (Math.abs(diff - Math.round(diff)) < 0.02f) {
                        g.draw(new Line2D.Double(
                                center.x + (radius + 6) * Math.cos(angle * Math.PI * 2d),
                                center.y - (radius + 6) * Math.sin(angle * Math.PI * 2d),
                                center.x + (radius - 2) * Math.cos(angle * Math.PI * 2d),
                                center.y - (radius - 2) * Math.sin(angle * Math.PI * 2d)));
                        } else {
                        
                        g.draw(new Line2D.Double(
                                center.x + (radius) * Math.cos(angle * Math.PI * 2d),
                                center.y - (radius) * Math.sin(angle * Math.PI * 2d),
                                center.x + (radius - 1) * Math.cos(angle * Math.PI * 2d),
                                center.y - (radius - 1) * Math.sin(angle * Math.PI * 2d)));
                        }
                    }
                }
            }
        }
    }

    public void setSelectedIndex(int newValue) {
        int oldValue = selectedIndex;
        selectedIndex = newValue;
        firePropertyChange(SELECTED_INDEX_PROPERTY, oldValue, newValue);
        repaint();
    }

    public int getSelectedIndex() {
        return selectedIndex;
    }

    protected Point getColorLocation(CompositeColor c) {
        Point p = colorWheelProducer.getColorLocation(c,
                getWidth() - wheelInsets.left - wheelInsets.right,
                getHeight() - wheelInsets.top - wheelInsets.bottom);
        p.x += wheelInsets.left;
        p.y += wheelInsets.top;
        return p;
    }

    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        setLayout(new java.awt.FlowLayout());
    }// </editor-fold>//GEN-END:initComponents
    // Variables declaration - do not modify//GEN-BEGIN:variables
    // End of variables declaration//GEN-END:variables
}

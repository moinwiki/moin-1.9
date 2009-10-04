/*
 * @(#)JColorWheel.java
 *
 * Copyright (c) 2007-2008 by the original authors of JHotDraw
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
import javax.swing.*;
import javax.swing.event.*;

/**
 * The JColorWheel displays a hue/saturation wheel of an HSL or an HSV ColorSystem. 
 * The user can click at the wheel to pick a color on the JColorWheel. 
 * The JColorWheel should be used together with a color slider for HSL luminance
 * or HSV value.
 *
 * @author  Werner Randelshofer
 * @version $Id: JColorWheel.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class JColorWheel extends JPanel {
    private ColorSystem sys;
    protected Insets wheelInsets;
    protected Image colorWheelImage;
    protected ColorWheelImageProducer colorWheelProducer;
    protected ColorSliderModel model;
    /** Radial color component index. */
    protected int radialIndex = 1;
    /** Angular color component index. */
    protected int angularIndex = 0;
    /** Vertical color component index. */
    protected int verticalIndex = 2;

    private class MouseHandler extends MouseAdapter implements MouseMotionListener  {
        public void mouseDragged(MouseEvent e) {
            update(e);
        }

        @Override
        public void mousePressed(MouseEvent e) {
            update(e);
        }

        @Override
        public void mouseReleased(MouseEvent e) {
            update(e);
        }

        private void update(MouseEvent e) {
            float[] hsb = getColorAt(e.getX(), e.getY());
            model.setComponentValue(angularIndex, hsb[angularIndex]);
            model.setComponentValue(radialIndex, hsb[radialIndex]);

            // FIXME - We should only repaint the damaged area
            repaint();
        }

        public void mouseMoved(MouseEvent e) {
            throw new UnsupportedOperationException("Not supported yet.");
        }
    }
    private MouseHandler mouseHandler;

    private class ModelHandler implements ChangeListener {

        public void stateChanged(ChangeEvent e) {
            repaint();
        }
    }
    private ModelHandler modelHandler;

    /**
     * Creates a new instance.
     */
    public JColorWheel() {
        this(new HSVRGBColorSystem());
        }
    public JColorWheel(ColorSystem sys) {
        this.sys = sys;
        wheelInsets = new Insets(0,0,0,0);
        model = new DefaultColorSliderModel(sys);
        initComponents();
        colorWheelProducer = createWheelProducer(0, 0);
        modelHandler = new ModelHandler();
        model.addChangeListener(modelHandler);
        installMouseListeners();
        setOpaque(false);
    }
    
    protected void installMouseListeners() {
        mouseHandler = new MouseHandler();
        addMouseListener(mouseHandler);
        addMouseMotionListener(mouseHandler);
    }

    public void setModel(ColorSliderModel m) {
        if (model != null) {
            model.removeChangeListener(modelHandler);
        }
        model = m;
        if (model != null) {
            model.addChangeListener(modelHandler);
        colorWheelProducer = createWheelProducer(getWidth(), getHeight());
            repaint();
        }
    }
    public void setRadialComponentIndex(int newValue) {
        radialIndex = newValue;
        colorWheelImage = null;
        repaint();
    }
    public void setAngularComponentIndex(int newValue) {
        angularIndex = newValue;
        colorWheelImage = null;
        repaint();
    }
    public void setVerticalComponentIndex(int newValue) {
        verticalIndex = newValue;
        colorWheelImage = null;
        repaint();
    }
    
    public void setWheelInsets(Insets newValue) {
        wheelInsets = newValue;
        repaint();
    }
    public Insets getWheelInsets() {
        return wheelInsets;
    }

    public Dimension getPreferredSize() {
        return new Dimension(100, 100);
    }

    public ColorSliderModel getModel() {
        return model;
    }

    public void paintComponent(Graphics gr) {
        Graphics2D g = (Graphics2D) gr;
        paintWheel(g);
        paintThumb(g);
    }

    protected ColorWheelImageProducer createWheelProducer(int w, int h) {
        ColorWheelImageProducer p = new ColorWheelImageProducer(model.getColorSystem(), w, h);
        p.setAngularComponentIndex(angularIndex);
        p.setRadialComponentIndex(radialIndex);
        p.setVerticalComponentIndex(verticalIndex);
        return p;
    }
    
    protected void paintWheel(Graphics2D g) {
        int w = getWidth() - wheelInsets.left - wheelInsets.right;
        int h = getHeight() - wheelInsets.top - wheelInsets.bottom;

        if (colorWheelImage == null || colorWheelImage.getWidth(this) != w || colorWheelImage.getHeight(this) != h) {
            if (colorWheelImage != null) {
                colorWheelImage.flush();
            }
            colorWheelProducer = createWheelProducer(w, h);
            colorWheelImage = createImage(colorWheelProducer);
        }

        colorWheelProducer.setVerticalValue(model.getComponentValue(verticalIndex));
        colorWheelProducer.regenerateColorWheel();

        g.drawImage(colorWheelImage, wheelInsets.left, wheelInsets.top, this);
    }

    protected void paintThumb(Graphics2D g) {
        Point p = getThumbLocation();

        g.setColor(Color.white);
        g.fillRect(p.x - 1, p.y - 1, 2, 2);
        g.setColor(Color.black);
        g.drawRect(p.x - 2, p.y - 2, 3, 3);
    }

    protected Point getCenter() {
        int w = getWidth() - wheelInsets.left - wheelInsets.right;
        int h = getHeight() - wheelInsets.top - wheelInsets.bottom;

        return new Point(
                wheelInsets.left + w / 2,
                wheelInsets.top + h / 2);
    }
    protected int getRadius() {
        return colorWheelProducer.getRadius();
    }
    protected Point getThumbLocation() {
        return getColorLocation(
                model.getComponentValue(0),
                model.getComponentValue(1),
                model.getComponentValue(2));
    }

    protected Point getColorLocation(Color c) {
        Point p = colorWheelProducer.getColorLocation(c, 
                getWidth() - wheelInsets.left - wheelInsets.right,
                getHeight() - wheelInsets.top - wheelInsets.bottom);
        p.x += wheelInsets.left;
        p.y += wheelInsets.top;
        return p;
    }

    protected Point getColorLocation(float hue, float saturation, float brightness) {
        Point p = colorWheelProducer.getColorLocation(hue, saturation, brightness, 
                getWidth() - wheelInsets.left - wheelInsets.right,
                getHeight() - wheelInsets.top - wheelInsets.bottom);
        p.x += wheelInsets.left;
        p.y += wheelInsets.top;
        return p;
    }

    protected float[] getColorAt(int x, int y) {
float[] cc = colorWheelProducer.getColorAt(x - wheelInsets.left, y - wheelInsets.top,
                getWidth() - wheelInsets.left - wheelInsets.right,
                getHeight() - wheelInsets.top - wheelInsets.bottom);        
        return cc;
    }

    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        setLayout(new java.awt.BorderLayout());
    }// </editor-fold>//GEN-END:initComponents
    // Variables declaration - do not modify//GEN-BEGIN:variables
    // End of variables declaration//GEN-END:variables
}

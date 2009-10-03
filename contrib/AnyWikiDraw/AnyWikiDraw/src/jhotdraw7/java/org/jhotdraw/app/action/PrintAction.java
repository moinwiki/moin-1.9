/*
 * @(#)PrintAction.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.app.action;

import java.awt.*;
import java.awt.event.*;
import java.awt.image.*;
import java.awt.print.*;
import javax.print.attribute.*;
import javax.print.attribute.standard.*;
import javax.swing.*;
import org.jhotdraw.app.*;
import org.jhotdraw.gui.*;
import org.jhotdraw.util.*;

/**
 * Presents a printer chooser to the user and then prints the
 * {@link org.jhotdraw.app.View}.
 * <p>
 * This action requires that the view implements the {@link PrintableView}
 * interface.
 * <p>
 * <hr>
 * <b>Design Patterns</b>
 *
 * <p><em>Framework</em><br>
 * The interfaces and classes listed below define together the contracts
 * of a smaller framework inside of the JHotDraw framework for document oriented
 * applications.<br>
 * Contract: {@link PrintableView}, {@link org.jhotdraw.app.action.PrintAction}.
 * <hr>
 *
 * @author Werner Randelshofer
 * @version $Id: PrintAction.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class PrintAction extends AbstractViewAction {

    public final static String ID = "file.print";

    /** Creates a new instance. */
    public PrintAction(Application app) {
        super(app);
        ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
        labels.configureAction(this, ID);
    }

    public void actionPerformed(ActionEvent evt) {
        View view = getActiveView();
        view.setEnabled(false);
        if (System.getProperty("apple.awt.graphics.UseQuartz", "false").equals("true")) {
            printQuartz();
        } else {
            printJava2D();
        }
        view.setEnabled(true);
    }
    /*
     * This prints at 72 DPI only. We might need this for some JVM versions on
     * Mac OS X.*/

    public void printJava2D() {
        Pageable pageable = ((PrintableView) getActiveView()).createPageable();
        if (pageable == null) {
            throw new InternalError("View does not have a method named java.awt.Pageable createPageable()");
        }

        try {
            PrinterJob job = PrinterJob.getPrinterJob();
            // FIXME - PrintRequestAttributeSet should be retrieved from View
            PrintRequestAttributeSet attr = new HashPrintRequestAttributeSet();
            attr.add(new PrinterResolution(300, 300, PrinterResolution.DPI));
            job.setPageable(pageable);
            if (job.printDialog()) {
                try {
                    job.print();
                } catch (PrinterException e) {
                    String message = (e.getMessage() == null) ? e.toString() : e.getMessage();
                    View view = getActiveView();
                    ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
                    JSheet.showMessageSheet(view.getComponent(),
                            "<html>" + UIManager.getString("OptionPane.css") +
                            "<b>" + labels.getString("couldntPrint") + "</b><br>" +
                            ((message == null) ? "" : message));
                }
            } else {
                System.out.println("JOB ABORTED!");
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }
    /*
     * This prints at 72 DPI only. We might need this for some JVM versions on
     * Mac OS X.*/

    public void printJava2DAlternative() {
        Pageable pageable = (Pageable) Methods.invokeGetter(getActiveView(), "createPageable", null);
        if (pageable == null) {
            throw new InternalError("View does not have a method named java.awt.Pageable createPageable()");
        }

        try {
            final PrinterJob job = PrinterJob.getPrinterJob();
            PrintRequestAttributeSet attr = new HashPrintRequestAttributeSet();
            attr.add(new PrinterResolution(300, 300, PrinterResolution.DPI));
            job.setPageable(pageable);
            if (job.printDialog(attr)) {
                try {
                    job.print();
                } catch (PrinterException e) {
                    ResourceBundleUtil labels = ResourceBundleUtil.getBundle("org.jhotdraw.app.Labels");
                    JSheet.showMessageSheet(getActiveView().getComponent(),
                            labels.getFormatted("couldntPrint", e));
                }
            } else {
                System.out.println("JOB ABORTED!");
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

    /**
     * On Mac OS X with the Quartz rendering engine, the following code achieves
     * the best results.
     */
    public void printQuartz() {
        Frame frame = (Frame) SwingUtilities.getWindowAncestor(getActiveView().getComponent());
        final Pageable pageable = (Pageable) Methods.invokeGetter(getActiveView(), "createPageable", null);
        final double resolution = 300d;
        JobAttributes jobAttr = new JobAttributes();
        // FIXME - PageAttributes should be retrieved from View
        PageAttributes pageAttr = new PageAttributes();
        pageAttr.setMedia(PageAttributes.MediaType.A4);
        pageAttr.setPrinterResolution((int) resolution);
        final PrintJob pj = frame.getToolkit().getPrintJob(
                frame,
                "Job Title",
                jobAttr,
                pageAttr);

        getActiveView().setEnabled(false);
        new Worker() {

            public Object construct() {

                // Compute page format from settings of the print job
                Paper paper = new Paper();
                paper.setSize(
                        pj.getPageDimension().width / resolution * 72d,
                        pj.getPageDimension().height / resolution * 72d);
                paper.setImageableArea(64d, 32d, paper.getWidth() - 96d, paper.getHeight() - 64);
                PageFormat pageFormat = new PageFormat();
                pageFormat.setPaper(paper);

                // Print the job
                try {
                    for (int i = 0,  n = pageable.getNumberOfPages(); i < n; i++) {
                        PageFormat pf = pageable.getPageFormat(i);
                        pf = pageFormat;
                        Graphics g = pj.getGraphics();
                        if (g instanceof Graphics2D) {
                            pageable.getPrintable(i).print(g, pf, i);
                        } else {
                            BufferedImage buf = new BufferedImage(
                                    (int) (pf.getImageableWidth() * resolution / 72d),
                                    (int) (pf.getImageableHeight() * resolution / 72d),
                                    BufferedImage.TYPE_INT_RGB);
                            Graphics2D bufG = buf.createGraphics();


                            bufG.setBackground(Color.WHITE);
                            bufG.fillRect(0, 0, buf.getWidth(), buf.getHeight());
                            bufG.scale(resolution / 72d, resolution / 72d);
                            bufG.translate(-pf.getImageableX(), -pf.getImageableY());
                            pageable.getPrintable(i).print(bufG, pf, i);
                            bufG.dispose();
                            g.drawImage(buf,
                                    (int) (pf.getImageableX() * resolution / 72d),
                                    (int) (pf.getImageableY() * resolution / 72d),
                                    null);
                            buf.flush();
                        }
                        g.dispose();
                    }
                } catch (Throwable t) {
                    t.printStackTrace();
                } finally {
                    pj.end();
                }
                return null;
            }

            public void finished(Object value) {
                getActiveView().setEnabled(true);
            }
        }.start();
    }
    /**
     * Returns true if the action is enabled.
     * The enabled state of the action depends on the state that has been set
     * using setEnabled() and on the enabled state of the application.
     *
     * @return true if the action is enabled, false otherwise
     * @see Action#isEnabled
     */
    @Override public boolean isEnabled() {
        return super.isEnabled() && (getActiveView() instanceof PrintableView);
    }
}

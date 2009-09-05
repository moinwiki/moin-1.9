/*
 * @(#)BidirectionalConnectionTool.java
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

package org.jhotdraw.draw;

import org.jhotdraw.undo.*;
import java.awt.*;
import java.awt.geom.*;
import java.awt.event.*;
import java.util.*;

/**
 * A tool that can be used to connect figures, to split
 * connections, and to join two segments of a connection.
 * ConnectionTools turns the visibility of the Connectors
 * on when it enters a figure.
 * The connection object to be created is specified by a prototype.
 * <p>
 * FIXME: Use a Tracker instance for each state of this tool.
 * <p>
 * XXX - This tool is not needed anywhere. We should get rid of it.
 *
 * @author Werner Randelshofer
 * @version $Id: BidirectionalConnectionTool.java 536 2009-06-14 12:10:57Z rawcoder $
 */
public class BidirectionalConnectionTool extends AbstractTool implements FigureListener {
    private Map<AttributeKey, Object> attributes;
    /**
     * the anchor point of the interaction
     */
    private Connector   startConnector;
    private Connector   endConnector;
    private Connector   targetConnector;
    
    private Figure target;
    /**
     * the currently created figure
     */
    private ConnectionFigure  connection;
    
    /**
     * the currently manipulated connection point
     */
    private int  splitPoint;
    /**
     * the currently edited connection
     */
    private ConnectionFigure  editedConnection;
    
    /**
     * the figure that was actually added
     * Note, this can be a different figure from the one which has been created.
     */
    private Figure createdFigure;
    
    /**
     * the prototypical figure that is used to create new
     * connections.
     */
    private ConnectionFigure  prototype;
    
    
    
    /** Creates a new instance. */
    public BidirectionalConnectionTool(ConnectionFigure prototype) {
        this.prototype = prototype;
    }
    public BidirectionalConnectionTool(ConnectionFigure prototype, Map<AttributeKey, Object> attributes) {
        this.prototype = prototype;
        this.attributes = attributes;
    }
    
    public void mouseMoved(MouseEvent evt) {
        trackConnectors(evt);
    }
    /**
     * Manipulates connections in a context dependent way. If the
     * mouse down hits a figure start a new connection. If the mousedown
     * hits a connection split a segment or join two segments.
     */
    public void mousePressed(MouseEvent evt) {
        super.mousePressed(evt);
        Point2D.Double ap = viewToDrawing(anchor);
        setTargetFigure(findConnectionStart(ap, getDrawing()));
        
        if (getTargetFigure() != null) {
            setStartConnector(findConnector(ap, target, prototype));
            if (getStartConnector() != null && prototype.canConnect(getTargetConnector())) {
                Point2D.Double p = getStartConnector().getAnchor();
                setConnection(createFigure());
                ConnectionFigure cf = getConnection();
                cf.setBounds(p, p);
                cf.addFigureListener(this);
                setCreatedFigure(cf);
            }
        }
    }
    
    /**
     * Adjust the created connection or split segment.
     */
    public void mouseDragged(java.awt.event.MouseEvent e) {
        Point2D.Double p = viewToDrawing(new Point(e.getX(), e.getY()));
        if (getConnection() != null) {
            trackConnectors(e);
            
            if (getTargetConnector() != null) {
                p = getTargetConnector().getAnchor();
            }
            getConnection().setEndPoint(p);
        } else if (editedConnection != null) {
            editedConnection.setPoint(splitPoint, p);
        }
    }
    /**
     * Connects the figures if the mouse is released over another
     * figure.
     */
    public void mouseReleased(MouseEvent e) {
        Figure c = null;
            Point2D.Double p = viewToDrawing(new Point(e.getX(), e.getY()));
        if (getStartConnector() != null) {
            c = findTarget(p, getDrawing());
        }
        
        if (c != null) {
            setEndConnector(findConnector(p, c, prototype));
            if (getEndConnector() != null) {
                CompositeEdit creationEdit = new CompositeEdit("Verbindung erstellen");
                getDrawing().fireUndoableEditHappened(creationEdit);
                getDrawing().add(getConnection());
                if (getConnection().canConnect(getStartConnector(), getEndConnector())) {
                    getConnection().setStartConnector(getStartConnector());
                    getConnection().setEndConnector(getEndConnector());
                } else {
                    getConnection().setStartConnector(getEndConnector());
                    getConnection().setEndConnector(getStartConnector());
                }
                getConnection().updateConnection();
                getConnection().removeFigureListener(this);
                getDrawing().fireUndoableEditHappened(creationEdit);
            }
        } else if (getConnection() != null) {
            getDrawing().remove(getConnection());
        }
        
        setConnection(null);
        setStartConnector(null);
        setEndConnector(null);
        setCreatedFigure(null);
        fireToolDone();
    }
    @Override
    public void activate(DrawingEditor editor) {
        super.activate(editor);
        getView().clearSelection();
    }
    @Override
    public void deactivate(DrawingEditor editor) {
        super.deactivate(editor);
    }
    //--
    /**
     * Creates the ConnectionFigure. By default the figure prototype is
     * cloned.
     */
    @SuppressWarnings("unchecked")
    protected ConnectionFigure createFigure() {
        ConnectionFigure f = (ConnectionFigure) prototype.clone();
        getEditor().applyDefaultAttributesTo(f);
        if (attributes != null) {
            for (Map.Entry<AttributeKey, Object> entry : attributes.entrySet()) {
                entry.getKey().basicSet(f, entry.getValue());
            }
        }
        return f;
    }
    
    /**
     * Finds a connectable figure target.
     */
    protected Figure findSource(Point2D.Double p, Drawing drawing) {
        return findConnectableFigure(p, drawing);
    }
    
    /**
     * Finds a connectable figure target.
     */
    protected Figure findTarget(Point2D.Double p, Drawing drawing) {
        Figure target = findConnectableFigure(p, drawing);
        Connector targetConnector = (target == null) ? null : target.findConnector(p, prototype);
        Connector startConnector = getStartConnector();
        
        if (targetConnector != null
        && getConnection() != null
        && target.canConnect()
        && (getConnection().canConnect(startConnector, targetConnector) || 
                getConnection().canConnect(targetConnector, startConnector))
        ) {
            return target;
        }
        return null;
    }
    
    /**
     * Finds an existing connection figure.
     */
    protected ConnectionFigure findConnection(Point2D.Double p, Drawing drawing) {
        for (Figure f : drawing.getFiguresFrontToBack()) {
            Figure fInside = f.findFigureInside(p);
            if (fInside != null && (fInside instanceof ConnectionFigure)) {
                return (ConnectionFigure) fInside;
            }
        }
        return null;
    }
    
    private void setConnection(ConnectionFigure newConnection) {
        connection = newConnection;
    }
    
    /**
     * Gets the connection which is created by this tool
     */
    protected ConnectionFigure getConnection() {
        return connection;
    }
    
    protected void trackConnectors(MouseEvent e) {
            Point2D.Double p = viewToDrawing(new Point(e.getX(), e.getY()));
        Figure c = null;
        
        if (getStartConnector() == null) {
            c = findSource(p, getDrawing());
        }
        else {
            c = findTarget(p, getDrawing());
        }
        Connector cc = null;
        if (c != null) {
            cc = findConnector(p, c, prototype);
        }
        if (cc != getTargetConnector()) {
            setTargetConnector(cc);
        }
        
        // track the figure containing the mouse
        if (c != getTargetFigure()) {
            setTargetFigure(c);
            Connector targetConnector = getTargetConnector();
        }
    }
    public void draw(Graphics2D g) {
        if (createdFigure != null) {
            createdFigure.draw(g);
        }
    }
    
    private Connector findConnector(Point2D.Double p, Figure target, ConnectionFigure f) {
        return target.findConnector(p, f);
    }
    
    /**
     * Finds a connection start figure.
     */
    protected Figure findConnectionStart(Point2D.Double p, Drawing drawing) {
        Figure target = findConnectableFigure(p, drawing);
        if ((target != null) && target.canConnect()) {
            return target;
        }
        return null;
    }
    
    private Figure findConnectableFigure(Point2D.Double p, Drawing drawing) {
        return drawing.findFigureExcept(p, createdFigure);
    }
    
    private void setStartConnector(Connector newStartConnector) {
        startConnector = newStartConnector;
    }
    
    protected Connector getStartConnector() {
        return startConnector;
    }
    
    private void setEndConnector(Connector newEndConnector) {
        endConnector = newEndConnector;
    }
    
    protected Connector getEndConnector() {
        return endConnector;
    }
    
    private void setTargetConnector(Connector newTargetConnector) {
        targetConnector = newTargetConnector;
    }
    
    protected Connector getTargetConnector() {
        return targetConnector;
    }
    
    private void setTargetFigure(Figure newTarget) {
        target = newTarget;
    }
    
    protected Figure getTargetFigure() {
        return target;
    }
    
    /**
     * Gets the figure that was actually added
     * Note, this can be a different figure from the one which has been created.
     */
    protected Figure getCreatedFigure() {
        return createdFigure;
    }
    
    private void setCreatedFigure(Figure newCreatedFigure) {
        createdFigure = newCreatedFigure;
    }
    
    public void areaInvalidated(FigureEvent evt) {
        fireAreaInvalidated(evt.getInvalidatedArea());
    }
    
    public void figureAdded(FigureEvent e) {
    }
    
    public void figureChanged(FigureEvent e) {
    }
    
    public void figureRemoved(FigureEvent e) {
    }
    
    public void figureRequestRemove(FigureEvent e) {
    }
    
    public void attributeChanged(FigureEvent e) {
    }

    public void figureHandlesChanged(FigureEvent e) {
    }
    
}

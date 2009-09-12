/*
 * @(#)TaskFigure.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.samples.pert.figures;

import java.io.IOException;
import java.awt.geom.*;
import static org.jhotdraw.draw.AttributeKeys.*;
import java.util.*;
import org.jhotdraw.draw.*;
import org.jhotdraw.geom.*;
import org.jhotdraw.util.*;
import org.jhotdraw.xml.*;

/**
 * TaskFigure.
 *
 * @author Werner Randelshofer.
 * @version $Id: TaskFigure.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class TaskFigure extends GraphicalCompositeFigure {

    private HashSet<DependencyFigure> dependencies;

    /**
     * This adapter is used, to connect a TextFigure with the name of
     * the TaskFigure model.
     */
    private static class NameAdapter extends FigureAdapter {

        private TaskFigure target;

        public NameAdapter(TaskFigure target) {
            this.target = target;
        }

        @Override
        public void attributeChanged(FigureEvent e) {
            // We could fire a property change event here, in case
            // some other object would like to observe us.
            //target.firePropertyChange("name", e.getOldValue(), e.getNewValue());
        }
    }

    private static class DurationAdapter extends FigureAdapter {

        private TaskFigure target;

        public DurationAdapter(TaskFigure target) {
            this.target = target;
        }

        @Override
        public void attributeChanged(FigureEvent evt) {
            // We could fire a property change event here, in case
            // some other object would like to observe us.
            //target.firePropertyChange("duration", e.getOldValue(), e.getNewValue());
            for (TaskFigure succ : target.getSuccessors()) {
                succ.updateStartTime();
            }
        }
    }

    /** Creates a new instance. */
    public TaskFigure() {
        super(new RectangleFigure());

        setLayouter(new VerticalLayouter());

        RectangleFigure nameCompartmentPF = new RectangleFigure();
        STROKE_COLOR.basicSet(nameCompartmentPF, null);
        nameCompartmentPF.setAttributeEnabled(STROKE_COLOR, false);
        FILL_COLOR.basicSet(nameCompartmentPF, null);
        nameCompartmentPF.setAttributeEnabled(FILL_COLOR, false);
        ListFigure nameCompartment = new ListFigure(nameCompartmentPF);
        ListFigure attributeCompartment = new ListFigure();
        SeparatorLineFigure separator1 = new SeparatorLineFigure();

        applyAttributes(getPresentationFigure());

        add(nameCompartment);
        add(separator1);
        add(attributeCompartment);

        Insets2D.Double insets = new Insets2D.Double(4, 8, 4, 8);
        LAYOUT_INSETS.basicSet(nameCompartment, insets);
        LAYOUT_INSETS.basicSet(attributeCompartment, insets);

        TextFigure nameFigure;
        nameCompartment.add(nameFigure = new TextFigure());
        FONT_BOLD.basicSet(nameFigure, true);
        nameFigure.setAttributeEnabled(FONT_BOLD, false);

        TextFigure durationFigure;
        attributeCompartment.add(durationFigure = new TextFigure());
        FONT_BOLD.basicSet(durationFigure, true);
        durationFigure.setText("0");
        durationFigure.setAttributeEnabled(FONT_BOLD, false);

        TextFigure startTimeFigure;
        attributeCompartment.add(startTimeFigure = new TextFigure());
        startTimeFigure.setEditable(false);
        startTimeFigure.setText("0");
        startTimeFigure.setAttributeEnabled(FONT_BOLD, false);

        applyAttributes(this);
        setAttributeEnabled(STROKE_DASHES, false);

        ResourceBundleUtil labels =
                ResourceBundleUtil.getBundle("org.jhotdraw.samples.pert.Labels");

        setName(labels.getString("pert.task.defaultName"));
        setDuration(0);

        dependencies = new HashSet<DependencyFigure>();
        nameFigure.addFigureListener(new NameAdapter(this));
        durationFigure.addFigureListener(new DurationAdapter(this));
    }

    @Override
    public Collection<Handle> createHandles(int detailLevel) {
        java.util.List<Handle> handles = new LinkedList<Handle>();
        switch (detailLevel) {
            case -1:
                handles.add(new BoundsOutlineHandle(getPresentationFigure(), false, true));
                break;
            case 0:
                handles.add(new MoveHandle(this, RelativeLocator.northWest()));
                handles.add(new MoveHandle(this, RelativeLocator.northEast()));
                handles.add(new MoveHandle(this, RelativeLocator.southWest()));
                handles.add(new MoveHandle(this, RelativeLocator.southEast()));
                handles.add(new ConnectorHandle(new LocatorConnector(this, RelativeLocator.east()), new DependencyFigure()));
                break;
        }
        return handles;
    }

    public void setName(String newValue) {
        getNameFigure().setText(newValue);
    }

    public String getName() {
        return getNameFigure().getText();
    }

    public void setDuration(int newValue) {
        int oldValue = getDuration();
        getDurationFigure().setText(Integer.toString(newValue));
        if (oldValue != newValue) {
            for (TaskFigure succ : getSuccessors()) {
                succ.updateStartTime();
            }
        }
    }

    public int getDuration() {
        try {
            return Integer.valueOf(getDurationFigure().getText());
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    public void updateStartTime() {
        willChange();
        int oldValue = getStartTime();
        int newValue = 0;
        for (TaskFigure pre : getPredecessors()) {
            newValue = Math.max(newValue,
                    pre.getStartTime() + pre.getDuration());
        }
        getStartTimeFigure().setText(Integer.toString(newValue));
        if (newValue != oldValue) {
            for (TaskFigure succ : getSuccessors()) {
                // The if-statement here guards against
                // cyclic task dependencies. 
                if (!this.isDependentOf(succ)) {
                    succ.updateStartTime();
                }
            }
        }
        changed();
    }

    public int getStartTime() {
        try {
            return Integer.valueOf(getStartTimeFigure().getText());
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    private TextFigure getNameFigure() {
        return (TextFigure) ((ListFigure) getChild(0)).getChild(0);
    }

    private TextFigure getDurationFigure() {
        return (TextFigure) ((ListFigure) getChild(2)).getChild(0);
    }

    private TextFigure getStartTimeFigure() {
        return (TextFigure) ((ListFigure) getChild(2)).getChild(1);
    }

    @SuppressWarnings("unchecked")
    private void applyAttributes(Figure f) {
        Map<AttributeKey, Object> attr = ((AbstractAttributedFigure) getPresentationFigure()).getAttributes();
        for (Map.Entry<AttributeKey, Object> entry : attr.entrySet()) {
            entry.getKey().basicSet(f, entry.getValue());
        }
    }

    @Override
    public TaskFigure clone() {
        TaskFigure that = (TaskFigure) super.clone();
        that.dependencies = new HashSet<DependencyFigure>();
        that.getNameFigure().addFigureListener(new NameAdapter(that));
        that.getDurationFigure().addFigureListener(new DurationAdapter(that));
        that.updateStartTime();
        return that;
    }

    @Override
    public void read(DOMInput in) throws IOException {
        double x = in.getAttribute("x", 0d);
        double y = in.getAttribute("y", 0d);
        double w = in.getAttribute("w", 0d);
        double h = in.getAttribute("h", 0d);
        setBounds(new Point2D.Double(x, y), new Point2D.Double(x + w, y + h));
        readAttributes(in);
        in.openElement("model");
        in.openElement("name");
        setName((String) in.readObject());
        in.closeElement();
        in.openElement("duration");
        setDuration((Integer) in.readObject());
        in.closeElement();
        in.closeElement();
    }

    public void write(DOMOutput out) throws IOException {
        Rectangle2D.Double r = getBounds();
        out.addAttribute("x", r.x);
        out.addAttribute("y", r.y);
        writeAttributes(out);
        out.openElement("model");
        out.openElement("name");
        out.writeObject(getName());
        out.closeElement();
        out.openElement("duration");
        out.writeObject(getDuration());
        out.closeElement();
        out.closeElement();
    }

    public int getLayer() {
        return 0;
    }

    public Set<DependencyFigure> getDependencies() {
        return Collections.unmodifiableSet(dependencies);
    }

    public void addDependency(DependencyFigure f) {
        dependencies.add(f);
        updateStartTime();
    }

    public void removeDependency(DependencyFigure f) {
        dependencies.remove(f);
        updateStartTime();
    }

    /**
     * Returns dependent PertTasks which are directly connected via a
     * PertDependency to this TaskFigure.
     */
    public List<TaskFigure> getSuccessors() {
        LinkedList<TaskFigure> list = new LinkedList<TaskFigure>();
        for (DependencyFigure c : getDependencies()) {
            if (c.getStartFigure() == this) {
                list.add((TaskFigure) c.getEndFigure());
            }
        }
        return list;
    }

    /**
     * Returns predecessor PertTasks which are directly connected via a
     * PertDependency to this TaskFigure.
     */
    public List<TaskFigure> getPredecessors() {
        LinkedList<TaskFigure> list = new LinkedList<TaskFigure>();
        for (DependencyFigure c : getDependencies()) {
            if (c.getEndFigure() == this) {
                list.add((TaskFigure) c.getStartFigure());
            }
        }
        return list;
    }

    /**
     * Returns true, if the current task is a direct or
     * indirect dependent of the specified task.
     * If the dependency is cyclic, then this method returns true
     * if <code>this</code> is passed as a parameter and for every other
     * task in the cycle.
     */
    public boolean isDependentOf(TaskFigure t) {
        if (this == t) {
            return true;
        }
        for (TaskFigure pre : getPredecessors()) {
            if (pre.isDependentOf(t)) {
                return true;
            }
        }
        return false;
    }

    public String toString() {
        return "TaskFigure#" + hashCode() + " " + getName() + " " + getDuration() + " " + getStartTime();
    }
}


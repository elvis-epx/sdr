#ifndef __TASK_H
#define __TASK_H

class TaskCallable {
	virtual ~TaskCallable() {}
};

class TaskManager;

class Task {
public:
	Task(TaskManager *mgr, const char *name, long int when, bool (SchCallable::*callback)(const char*));
	~Task();
	bool should_run();
	bool run();
	void attach();
	void detach();
private:
	TaskManager *mgr;
	Buffer name;
	long int when;
	bool attached;
	bool (TaskCallable::*callback)(const char *);
};

class TaskManager {
public:
	TaskManager();
	bool run(long int time);
	void add(Task *task);
	void remove(Task *task);
private:
	Task* tasks[]; // note: weak reference (other party is owner)
};

#endif

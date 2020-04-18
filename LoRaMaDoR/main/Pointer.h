#ifndef __PTR_H
#define __PTR_H

template <class T> class PtrRef;

template <class T> class Ptr
{
public:
	inline Ptr()
	{
		payload = new PtrRef<T>(0);
	}

	explicit inline Ptr(T* parg)
	{
		payload = new PtrRef<T>(parg);
	}

	inline Ptr(const Ptr& arg) 
	{
		payload = arg.payload;
		++payload->refcount;
	}

	inline Ptr& operator=(const Ptr& outro) 
	{
		++outro.payload->refcount;
		if(--payload->refcount == 0) {
			delete payload;
		}
		payload = outro.payload;
		return *this;
	}

	inline ~Ptr() 
	{
		if (--payload->refcount == 0) {
			delete payload;
			payload = 0;
		}
	}

	inline T* operator->() const
	{
		return payload->pointer;
	}

	inline T& operator*() const
	{
		return *(payload->pointer);
	}

	inline bool operator!() const
	{
		return (payload->pointer == 0);
	}

	inline operator bool() const
	{
		return (payload->pointer != 0);
	}

	inline T* p() const
	{
		return payload->pointer;
	}

	inline const T* id() const
	{
		return payload->pointer;
	}

private:
	PtrRef<T>* payload;
};

template <class T> class PtrRef
{
	inline PtrRef(T* p)
	{
		pointer = p;
		refcount = 1;
	}

	inline ~PtrRef()
	{
		delete pointer;
		pointer = 0;
	}

	T* pointer;
	unsigned int refcount;

friend class Ptr<T>;
};

#endif


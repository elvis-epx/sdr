#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "Packet.h"

void test2()
{
	printf("---\n");
	Ptr<Packet> p = Packet::decode_l3("AAAA<BBBB:133");
	assert (!!p);
	assert (p->msg().length() == 0);

	p = Packet::decode_l3("AAAA-12<BBBB:133 ee");
	assert (!!p);
	assert (strcmp("ee", p->msg().cold()) == 0);
	assert (p->msg().str_equal("ee"));
	assert (strcmp(p->to(), "AAAA-12") == 0);
	
	assert (!Packet::decode_l3("AAAA:BBBB<133"));
	p = Packet::decode_l3("AAAA<BBBB:133,aaa,bbb=ccc,ddd=eee,fff bla");
	assert (!!p);

	assert (!Packet::decode_l3("AAAA<BBBB:133,aaa,,ddd=eee,fff bla"));
	assert (!Packet::decode_l3("AAAA<BBBB:01 bla"));
	assert (!Packet::decode_l3("AAAA<BBBB:aa bla"));

	p = Packet::decode_l3("AAAA<BBBB:133,A,B=C bla");
	assert (!!p);
	Ptr<Packet> q = p->change_msg("bla ble");
	Params d = q->params();
	d.put("E", None);
	d.put("F", "G");
	Ptr<Packet> r = p->change_params(d);
	assert(r->params().has("A"));
	assert(r->params().has("B"));
	assert(r->params().get("A").str_equal(None));
	assert(! r->params().get("B").str_equal(None));
	assert(r->params().get("B").str_equal("C"));

	assert(!q->params().has("E"));
	assert(!q->params().has("F"));

	assert(r->params().has("E"));
	assert(r->params().get("E").str_equal(None));
	assert(r->params().has("F"));
	assert(! r->params().get("F").str_equal(None));
	assert(strcmp(r->params().get("F").cold(), "G") == 0);

	assert(strcmp(q->msg().cold(), "bla ble") == 0);
	assert(strcmp(r->msg().cold(), "bla") == 0);
}

void test3()
{
	unsigned long int ident;
	Params params;

	assert(Packet::parse_params("1234", ident, params));
	assert (ident == 1234);
	assert(Packet::parse_params("1235,abc", ident, params));
	assert (ident == 1235);
	assert(params.has("ABC"));
	printf("ABC=%s\n", params.get("ABC").cold());
	assert(params.get("ABC").str_equal(None));

	assert(Packet::parse_params("1236,abc,def=ghi", ident, params));
	assert (ident == 1236);
	assert(params.has("ABC"));
	assert(params.has("DEF"));
	assert(strcmp(params.get("DEF").cold(), "ghi") == 0);
	assert(params.count() == 2);

	assert(Packet::parse_params("def=ghi,1239", ident, params));
	assert (ident == 1239);
	assert (params.count() == 1);
	assert (params.has("DEF"));
	assert (strcmp(params.get("DEF").cold(), "ghi") == 0);

	assert (!Packet::parse_params("123a", ident, params));
	assert (!Packet::parse_params("0123", ident, params));
	assert (!Packet::parse_params("abc", ident, params));
	assert (!Packet::parse_params("abc=def", ident, params));
	assert (!Packet::parse_params("123,0bc=def", ident, params));
	assert (!Packet::parse_params("123,0bc", ident, params));
	assert (!Packet::parse_params("123,,bc", ident, params));
	assert (Packet::parse_params("1,abc=def", ident, params));
	assert (Packet::parse_params("1,2,abc=def", ident, params));
	assert (ident == 2);
	assert (!Packet::parse_params("1,,abc=def", ident, params));
	assert (!Packet::parse_params("1,a#c=def", ident, params));
	assert (!Packet::parse_params("1,a:c=d ef", ident, params));
	assert (!Packet::parse_params("1,ac=d ef", ident, params));
}

void test4()
{
	Vector<Buffer> a;
	a.push_back(Buffer("B"));
	a.push_back(Buffer("C"));
	a.push_back(Buffer("D"));
	a.remov(1);
	assert(a.size() == 2);
	assert(a[0].str_equal("B"));
	assert(a[1].str_equal("D"));
}

int main()
{
	assert (!Packet::check_callsign("Q"));
	assert (Packet::check_callsign("QB"));
	assert (Packet::check_callsign("QC"));
	assert (!Packet::check_callsign("Q1"));
	assert (!Packet::check_callsign("Q-"));
	assert (!Packet::check_callsign("qcc"));
	assert (!Packet::check_callsign("xc"));
	assert (!Packet::check_callsign("1cccc"));
	assert (!Packet::check_callsign("aaaaa-1a"));
	assert (!Packet::check_callsign("aaaaa-01"));
	assert (!Packet::check_callsign("a#jskd"));
	assert (!Packet::check_callsign("-1"));
	assert (!Packet::check_callsign("aaa-1"));
	assert (!Packet::check_callsign("aaaa-1-2"));;
	assert (!Packet::check_callsign("aaaa-123"));

	test3();

	Buffer bb("abcde");
	assert (bb.length() == 5);
	assert (strcmp(bb.cold(), "abcde") == 0);

	Params d;
	d.put("x", None);
	d.put("y", "456");
	Packet p = Packet("aaAA", "BBbB", 123, d, Buffer("bla ble"));
	Buffer spl3 = p.encode_l3();
	Buffer spl2 = p.encode_l2();

	printf("'%s'\n", spl3.cold());
	assert (strcmp(spl3.cold(), "AAAA<BBBB:123,X,Y=456 bla ble") == 0);
	printf("---\n");
	Ptr<Packet> q = Packet::decode_l2(spl2.cold(), spl2.length());
	assert (q);

	/* Corrupt some chars */
	spl2.hot()[1] = 66;
	spl2.hot()[3] = 66;
	spl2.hot()[7] = 66;
	spl2.hot()[9] = 66;
	spl2.hot()[12] = 66;
	spl2.hot()[15] = 66;
	spl2.hot()[33] = 66;
	spl2.hot()[40] = 66;
	q = Packet::decode_l2(spl2.cold(), spl2.length());
	assert (q);

	/* Corrupt too many chars */
	spl2.hot()[2] = 66;
	spl2.hot()[5] = 66;
	spl2.hot()[6] = 66;
	spl2.hot()[8] = 66;
	spl2.hot()[10] = 66;
	spl2.hot()[11] = 66;
	spl2.hot()[13] = 66;
	spl2.hot()[39] = 66;
	assert(! Packet::decode_l2(spl2.cold(), spl2.length()));

	assert (p.is_dup(*q));
	assert (q->is_dup(p));
	assert (strcmp(q->to(), "AAAA") == 0);
	assert (strcmp(q->from(), "BBBB") == 0);
	assert (q->ident() == 123);
	assert (q->params().has("X"));
	assert (q->params().has("Y"));
	assert (! q->params().has("Z"));
	assert (strcmp(q->params().get("Y").cold(), "456") == 0);
	assert (q->params().get("X").str_equal(None));

	test2();
	test4();

	printf("Autotest ok\n");
}

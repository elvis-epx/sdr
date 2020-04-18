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
	assert (strcmp(p->to().buf().cold(), "AAAA-12") == 0);
	
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
	d.put_naked("E");
	d.put("F", "G");
	Ptr<Packet> r = p->change_params(d);
	assert(r->params().has("A"));
	assert(r->params().has("B"));
	assert(r->params().is_key_naked("A"));
	assert(! r->params().is_key_naked("B"));
	assert(r->params().get("B").str_equal("C"));

	assert(!q->params().has("E"));
	assert(!q->params().has("F"));

	assert(r->params().has("E"));
	assert(r->params().is_key_naked("E"));
	assert(r->params().has("F"));
	assert(! r->params().is_key_naked("F"));
	assert(strcmp(r->params().get("F").cold(), "G") == 0);

	assert(strcmp(q->msg().cold(), "bla ble") == 0);
	assert(strcmp(r->msg().cold(), "bla") == 0);
}

void test3()
{
	Params params;

	params = Params("1234");
	assert (params.is_valid_with_ident());
	assert (params.ident() == 1234);
	params = Params("1235,abc");
	assert (params.is_valid_with_ident());
	assert (params.ident() == 1235);
	assert(params.has("ABC"));
	printf("ABC=%s\n", params.get("ABC").cold());
	assert(params.is_key_naked("ABC"));

	params = Params("1236,abc,def=ghi");
	assert (params.is_valid_with_ident());
	assert (params.ident() == 1236);
	assert(params.has("ABC"));
	assert(params.has("DEF"));
	assert(strcmp(params.get("DEF").cold(), "ghi") == 0);
	assert(params.count() == 2);

	params = Params("def=ghi,1239");
	assert (params.is_valid_with_ident());
	assert (params.ident() == 1239);
	assert (params.count() == 1);
	assert (params.has("DEF"));
	assert (strcmp(params.get("DEF").cold(), "ghi") == 0);

	assert (!Params("123a").is_valid_with_ident());
	assert (!Params("0123").is_valid_with_ident());
	assert (!Params("abc").is_valid_with_ident());
	assert (!Params("abc=def").is_valid_with_ident());
	assert (Params("abc=def").is_valid_without_ident());
	assert (!Params("123,0bc=def").is_valid_with_ident());
	assert (!Params("123,0bc").is_valid_with_ident());
	assert (!Params("123,,bc").is_valid_with_ident());
	assert (Params("1,abc=def").is_valid_with_ident());
	params = Params("1,2,abc=def");
	assert (params.is_valid_with_ident());
	assert (params.ident() == 2);
	assert (!Params("1,,abc=def").is_valid_with_ident());
	assert (!Params("1,a#c=def").is_valid_with_ident());
	assert (!Params("1,a:c=d ef").is_valid_with_ident());
	assert (!Params("1,ac=d ef").is_valid_with_ident());
	assert (Params("ac=d,e,f=").is_valid_without_ident());
	assert (Params("3,ac=d,e,f=").is_valid_without_ident());
	assert (!Params("3,ac=d,e, f=").is_valid_without_ident());
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

void test5()
{
	Dict<int> a;
	a["B"] = 2;
	a["Z"] = 26;
	a["A"] = 1;
	a["D"] = 4;
	a["G"] = 7;
	a["F"] = 6;

	assert(a["B"] == 2);
	assert(a["Z"] == 26);
	assert(a["A"] == 1);
	assert(a["D"] == 4);
	assert(a["G"] == 7);
	assert(a["F"] == 6);

	assert(a.indexOf("A") == 0);
	assert(a.indexOf("B") == 1);
	assert(a.indexOf("D") == 2);
	assert(a.indexOf("F") == 3);
	assert(a.indexOf("G") == 4);
	assert(a.indexOf("Z") == 5);

	a.remove("E");
	a.remove("A");
	assert(a.indexOf("Z") == 4);
}

int main()
{
	assert (!Callsign("Q").is_valid());
	assert (Callsign("QB").is_valid());
	assert (Callsign("QC").is_valid());
	assert (!Callsign("Q1").is_valid());
	assert (!Callsign("Q-").is_valid());
	assert (!Callsign("qcc").is_valid());
	assert (!Callsign("xc").is_valid());
	assert (!Callsign("1cccc").is_valid());
	assert (!Callsign("aaaaa-1a").is_valid());
	assert (!Callsign("aaaaa-01").is_valid());
	assert (!Callsign("a#jskd").is_valid());
	assert (!Callsign("-1").is_valid());
	assert (!Callsign("aaa-1").is_valid());
	assert (!Callsign("aaaa-1-2").is_valid());;
	assert (!Callsign("aaaa-123").is_valid());

	test3();

	Buffer bb("abcde");
	assert (bb.length() == 5);
	assert (strcmp(bb.cold(), "abcde") == 0);

	Params d;
	d.put_naked("x");
	d.put("y", "456");
	d.set_ident(123);
	Packet p = Packet(Callsign(Buffer("aaAA")), Callsign(Buffer("BBbB")), d, Buffer("bla ble"));
	Buffer spl3 = p.encode_l3();
	Buffer spl2 = p.encode_l2();

	printf("spl3 '%s'\n", spl3.cold());
	assert (strcmp(spl3.cold(), "AAAA<BBBB:123,X,Y=456 bla ble") == 0);
	printf("---\n");
	Ptr<Packet> q = Packet::decode_l2(spl2.cold(), spl2.length(), -50);
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
	q = Packet::decode_l2(spl2.cold(), spl2.length(), -50);
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
	assert(! Packet::decode_l2(spl2.cold(), spl2.length(), -50));

	assert (p.is_dup(*q));
	assert (q->is_dup(p));
	assert (strcmp(q->to().buf().cold(), "AAAA") == 0);
	assert (strcmp(q->from().buf().cold(), "BBBB") == 0);
	assert (q->params().ident() == 123);
	assert (q->params().has("X"));
	assert (q->params().has("Y"));
	assert (! q->params().has("Z"));
	assert (strcmp(q->params().get("Y").cold(), "456") == 0);
	assert (q->params().is_key_naked("X"));

	test2();
	test4();
	test5();

	printf("Autotest ok\n");
}

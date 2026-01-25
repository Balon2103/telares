--
-- PostgreSQL database dump
--

\restrict 4jSIVLzmuzoOxRMzWZ0m2amsyJrDKzcOUh6Scrj9myqoMRDSPmit7Xeiy2mi6kt

-- Dumped from database version 15.15 (Debian 15.15-1.pgdg13+1)
-- Dumped by pg_dump version 17.6 (Debian 17.6-0+deb13u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: enlaces; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.enlaces (
    id integer NOT NULL,
    origen integer NOT NULL,
    destino integer NOT NULL,
    tipo character varying(100),
    ancho_banda character varying(100)
);


ALTER TABLE public.enlaces OWNER TO postgres;

--
-- Name: enlaces_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.enlaces_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.enlaces_id_seq OWNER TO postgres;

--
-- Name: enlaces_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.enlaces_id_seq OWNED BY public.enlaces.id;


--
-- Name: nodos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.nodos (
    id integer NOT NULL,
    nombre character varying(100),
    ip character varying(50),
    tipo character varying(50),
    ubicacion text,
    rol text,
    pos_x double precision,
    pos_y double precision
);


ALTER TABLE public.nodos OWNER TO postgres;

--
-- Name: nodos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.nodos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nodos_id_seq OWNER TO postgres;

--
-- Name: nodos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.nodos_id_seq OWNED BY public.nodos.id;


--
-- Name: enlaces id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enlaces ALTER COLUMN id SET DEFAULT nextval('public.enlaces_id_seq'::regclass);


--
-- Name: nodos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nodos ALTER COLUMN id SET DEFAULT nextval('public.nodos_id_seq'::regclass);


--
-- Data for Name: enlaces; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.enlaces (id, origen, destino, tipo, ancho_banda) FROM stdin;
\.


--
-- Data for Name: nodos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.nodos (id, nombre, ip, tipo, ubicacion, rol, pos_x, pos_y) FROM stdin;
14	Jose Marquez	192.91.920.1	\N	Finanzas	router	0	0
\.


--
-- Name: enlaces_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.enlaces_id_seq', 1, true);


--
-- Name: nodos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.nodos_id_seq', 14, true);


--
-- Name: enlaces enlaces_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enlaces
    ADD CONSTRAINT enlaces_pkey PRIMARY KEY (id);


--
-- Name: nodos nodos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nodos
    ADD CONSTRAINT nodos_pkey PRIMARY KEY (id);


--
-- Name: enlaces enlaces_destino_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enlaces
    ADD CONSTRAINT enlaces_destino_fkey FOREIGN KEY (destino) REFERENCES public.nodos(id) ON DELETE CASCADE;


--
-- Name: enlaces enlaces_origen_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.enlaces
    ADD CONSTRAINT enlaces_origen_fkey FOREIGN KEY (origen) REFERENCES public.nodos(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 4jSIVLzmuzoOxRMzWZ0m2amsyJrDKzcOUh6Scrj9myqoMRDSPmit7Xeiy2mi6kt


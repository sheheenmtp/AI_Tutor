--
-- PostgreSQL database dump
--

\restrict pesFBFPUTbYGo07Uz2V6XQZapiBCmn5sbKAXoI5EtVMhbcx2ObJaelg6cnCv1vE

-- Dumped from database version 14.20 (Ubuntu 14.20-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.20 (Ubuntu 14.20-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: ai_feedback_logs; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.ai_feedback_logs (
    id integer NOT NULL,
    submission_id integer NOT NULL,
    prompt text,
    response text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.ai_feedback_logs OWNER TO codemastery_user;

--
-- Name: ai_feedback_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.ai_feedback_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ai_feedback_logs_id_seq OWNER TO codemastery_user;

--
-- Name: ai_feedback_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.ai_feedback_logs_id_seq OWNED BY public.ai_feedback_logs.id;


--
-- Name: concepts; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.concepts (
    id character varying(20) NOT NULL,
    name character varying(255) NOT NULL,
    axis character varying(100),
    level character varying(50),
    mental_model text,
    repair_strategy text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.concepts OWNER TO codemastery_user;

--
-- Name: diagnostic_logs; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.diagnostic_logs (
    id integer NOT NULL,
    submission_id integer NOT NULL,
    error_id character varying(50),
    concept_id character varying(20),
    confidence double precision,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.diagnostic_logs OWNER TO codemastery_user;

--
-- Name: diagnostic_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.diagnostic_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.diagnostic_logs_id_seq OWNER TO codemastery_user;

--
-- Name: diagnostic_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.diagnostic_logs_id_seq OWNED BY public.diagnostic_logs.id;


--
-- Name: errors; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.errors (
    id character varying(50) NOT NULL,
    concept_id character varying(20) NOT NULL,
    description text,
    signal_type character varying(100),
    confidence_weight double precision DEFAULT 0.8
);


ALTER TABLE public.errors OWNER TO codemastery_user;

--
-- Name: learner_concept_state; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.learner_concept_state (
    user_id integer NOT NULL,
    concept_id character varying(20) NOT NULL,
    mastery_score double precision DEFAULT 0.7,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.learner_concept_state OWNER TO codemastery_user;

--
-- Name: problems; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.problems (
    id integer NOT NULL,
    title text NOT NULL,
    description text NOT NULL,
    difficulty text NOT NULL,
    order_index integer NOT NULL,
    starter_code text,
    hints json,
    input_format text NOT NULL,
    output_format text NOT NULL,
    concept_id character varying(20)
);


ALTER TABLE public.problems OWNER TO codemastery_user;

--
-- Name: problems_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.problems_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.problems_id_seq OWNER TO codemastery_user;

--
-- Name: problems_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.problems_id_seq OWNED BY public.problems.id;


--
-- Name: submissions; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.submissions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    problem_id integer NOT NULL,
    code text NOT NULL,
    status character varying(20),
    passed_tests integer,
    total_tests integer,
    score integer,
    submitted_at timestamp without time zone
);


ALTER TABLE public.submissions OWNER TO codemastery_user;

--
-- Name: submissions_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.submissions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.submissions_id_seq OWNER TO codemastery_user;

--
-- Name: submissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.submissions_id_seq OWNED BY public.submissions.id;


--
-- Name: test_cases; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.test_cases (
    id integer NOT NULL,
    problem_id integer NOT NULL,
    input_data text,
    expected_output text NOT NULL,
    is_sample boolean,
    is_hidden boolean,
    points integer
);


ALTER TABLE public.test_cases OWNER TO codemastery_user;

--
-- Name: test_cases_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.test_cases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.test_cases_id_seq OWNER TO codemastery_user;

--
-- Name: test_cases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.test_cases_id_seq OWNED BY public.test_cases.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: codemastery_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(100) NOT NULL,
    current_level character varying(20),
    total_score integer,
    problems_solved integer,
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO codemastery_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: codemastery_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO codemastery_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codemastery_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: ai_feedback_logs id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.ai_feedback_logs ALTER COLUMN id SET DEFAULT nextval('public.ai_feedback_logs_id_seq'::regclass);


--
-- Name: diagnostic_logs id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.diagnostic_logs ALTER COLUMN id SET DEFAULT nextval('public.diagnostic_logs_id_seq'::regclass);


--
-- Name: problems id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.problems ALTER COLUMN id SET DEFAULT nextval('public.problems_id_seq'::regclass);


--
-- Name: submissions id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.submissions ALTER COLUMN id SET DEFAULT nextval('public.submissions_id_seq'::regclass);


--
-- Name: test_cases id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.test_cases ALTER COLUMN id SET DEFAULT nextval('public.test_cases_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: ai_feedback_logs ai_feedback_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.ai_feedback_logs
    ADD CONSTRAINT ai_feedback_logs_pkey PRIMARY KEY (id);


--
-- Name: concepts concepts_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.concepts
    ADD CONSTRAINT concepts_pkey PRIMARY KEY (id);


--
-- Name: diagnostic_logs diagnostic_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.diagnostic_logs
    ADD CONSTRAINT diagnostic_logs_pkey PRIMARY KEY (id);


--
-- Name: errors errors_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_pkey PRIMARY KEY (id);


--
-- Name: learner_concept_state learner_concept_state_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.learner_concept_state
    ADD CONSTRAINT learner_concept_state_pkey PRIMARY KEY (user_id, concept_id);


--
-- Name: problems problems_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.problems
    ADD CONSTRAINT problems_pkey PRIMARY KEY (id);


--
-- Name: submissions submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_pkey PRIMARY KEY (id);


--
-- Name: test_cases test_cases_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.test_cases
    ADD CONSTRAINT test_cases_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: ix_problems_id; Type: INDEX; Schema: public; Owner: codemastery_user
--

CREATE INDEX ix_problems_id ON public.problems USING btree (id);


--
-- Name: ix_submissions_id; Type: INDEX; Schema: public; Owner: codemastery_user
--

CREATE INDEX ix_submissions_id ON public.submissions USING btree (id);


--
-- Name: ix_test_cases_id; Type: INDEX; Schema: public; Owner: codemastery_user
--

CREATE INDEX ix_test_cases_id ON public.test_cases USING btree (id);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: codemastery_user
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ai_feedback_logs ai_feedback_logs_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.ai_feedback_logs
    ADD CONSTRAINT ai_feedback_logs_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) ON DELETE CASCADE;


--
-- Name: diagnostic_logs diagnostic_logs_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.diagnostic_logs
    ADD CONSTRAINT diagnostic_logs_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id);


--
-- Name: diagnostic_logs diagnostic_logs_error_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.diagnostic_logs
    ADD CONSTRAINT diagnostic_logs_error_id_fkey FOREIGN KEY (error_id) REFERENCES public.errors(id);


--
-- Name: diagnostic_logs diagnostic_logs_submission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.diagnostic_logs
    ADD CONSTRAINT diagnostic_logs_submission_id_fkey FOREIGN KEY (submission_id) REFERENCES public.submissions(id) ON DELETE CASCADE;


--
-- Name: errors errors_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.errors
    ADD CONSTRAINT errors_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id) ON DELETE CASCADE;


--
-- Name: problems fk_problem_concept; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.problems
    ADD CONSTRAINT fk_problem_concept FOREIGN KEY (concept_id) REFERENCES public.concepts(id) ON DELETE SET NULL;


--
-- Name: learner_concept_state learner_concept_state_concept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.learner_concept_state
    ADD CONSTRAINT learner_concept_state_concept_id_fkey FOREIGN KEY (concept_id) REFERENCES public.concepts(id) ON DELETE CASCADE;


--
-- Name: learner_concept_state learner_concept_state_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.learner_concept_state
    ADD CONSTRAINT learner_concept_state_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: submissions submissions_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_problem_id_fkey FOREIGN KEY (problem_id) REFERENCES public.problems(id);


--
-- Name: submissions submissions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: test_cases test_cases_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codemastery_user
--

ALTER TABLE ONLY public.test_cases
    ADD CONSTRAINT test_cases_problem_id_fkey FOREIGN KEY (problem_id) REFERENCES public.problems(id);


--
-- PostgreSQL database dump complete
--

\unrestrict pesFBFPUTbYGo07Uz2V6XQZapiBCmn5sbKAXoI5EtVMhbcx2ObJaelg6cnCv1vE

